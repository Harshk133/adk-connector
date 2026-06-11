import asyncio
import logging
import os
import json
import shutil
import subprocess
import secrets
from typing import Optional, Dict, Any
import websockets

from adk_connectors.base_adapter import BaseAdapter
from adk_connectors.models.incoming import IncomingMessage, MediaType
from adk_connectors.models.outgoing import OutgoingMessage
from adk_connectors.whatsapp.config import WhatsAppConfig

logger = logging.getLogger("adk_connectors.whatsapp")

class WhatsAppAdapter(BaseAdapter):
    platform = "whatsapp"

    def __init__(self, config: WhatsAppConfig):
        super().__init__()
        self.config = config
        self.bridge_proc: Optional[subprocess.Popen] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._listen_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self) -> None:
        self._is_running = True
        
        # 1. Setup default config paths and token if not set
        if not self.config.bridge_token:
            self.config.bridge_token = secrets.token_urlsafe(32)
            
        if not self.config.auth_dir:
            self.config.auth_dir = os.path.join(os.path.expanduser("~"), ".adk-whatsapp-auth")
            
        # 2. Build/Prepare Node.js dependencies
        bridge_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bridge')
        if not os.path.exists(os.path.join(bridge_dir, 'node_modules')):
            logger.info("Node.js dependencies not found. Running npm install...")
            npm_bin = shutil.which("npm")
            if not npm_bin:
                raise RuntimeError("npm is not installed on this system. Please install Node.js and npm.")
            subprocess.run([npm_bin, "install"], cwd=bridge_dir, check=True, shell=os.name == 'nt')
            
        # 3. Start bridge subprocess
        node_bin = shutil.which("node")
        if not node_bin:
            raise RuntimeError("node is not installed on this system. Please install Node.js.")
            
        bridge_script = os.path.join(bridge_dir, 'bridge.js')
        env = os.environ.copy()
        env["BRIDGE_PORT"] = str(self.config.port)
        env["BRIDGE_TOKEN"] = self.config.bridge_token
        env["AUTH_DIR"] = self.config.auth_dir
        
        logger.info(f"Launching WhatsApp Baileys bridge on port {self.config.port}...")
        self.bridge_proc = subprocess.Popen(
            [node_bin, bridge_script],
            cwd=bridge_dir,
            env=env,
            shell=os.name == 'nt'
        )
        
        # 4. Wait shortly and connect WebSocket client
        self._listen_task = asyncio.create_task(self._connect_and_listen())

    async def stop(self) -> None:
        self._is_running = False
        
        if self.ws:
            await self.ws.close()
            
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
                
        if self.bridge_proc:
            logger.info("Stopping WhatsApp bridge process...")
            self.bridge_proc.terminate()
            try:
                self.bridge_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                logger.warning("WhatsApp bridge process did not stop gracefully. Killing it...")
                self.bridge_proc.kill()
            self.bridge_proc = None

    async def _connect_and_listen(self) -> None:
        uri = f"ws://{self.config.host}:{self.config.port}"
        
        # Retry logic for connecting to the bridge server
        for attempt in range(5):
            if not self._is_running:
                return
            try:
                self.ws = await websockets.connect(uri)
                break
            except Exception as e:
                if attempt == 4:
                    logger.error(f"Could not connect to WhatsApp bridge at {uri}: {e}")
                    return
                await asyncio.sleep(1.0 * (attempt + 1))
                
        # Send auth handshake
        auth_payload = {
            "type": "auth",
            "token": self.config.bridge_token
        }
        await self.ws.send(json.dumps(auth_payload))
        
        # Start message loop
        while self._is_running:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                await self._handle_bridge_message(data)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection to WhatsApp bridge closed.")
                break
            except Exception as e:
                logger.error(f"Error in WhatsApp bridge connection: {e}")
                await asyncio.sleep(1)

    async def _handle_bridge_message(self, data: Dict[str, Any]) -> None:
        msg_type = data.get("type")
        
        if msg_type == "message":
            chat_id = data.get("sender")
            user_id = chat_id.split("@")[0]
            text = data.get("text")
            message_id = data.get("id")
            
            incoming = IncomingMessage(
                platform="whatsapp",
                user_id=str(user_id),
                chat_id=str(chat_id),
                message_id=str(message_id),
                text=text,
                media_type=MediaType.TEXT,
                raw_update=data
            )
            
            if self.on_message_callback:
                asyncio.create_task(self.on_message_callback(incoming))
                
        elif msg_type == "qr":
            logger.info("New WhatsApp Login QR Code generated in bridge.")
            
        elif msg_type == "connected":
            logger.info("Successfully authenticated with WhatsApp!")
            
        elif msg_type == "error":
            logger.error(f"WhatsApp bridge returned error: {data.get('message')}")

    async def send_message(self, chat_id: str, message: OutgoingMessage) -> Dict[str, Any]:
        if not self.ws:
            logger.error("Cannot send message: Not connected to WhatsApp bridge.")
            return {}
            
        text = message.text
        if message.inline_keyboard:
            buttons_text = []
            for row in message.inline_keyboard:
                for btn in row:
                    buttons_text.append(f"[{btn.text}]")
            if buttons_text:
                text += "\n\n" + "  ".join(buttons_text)
                
        payload = {
            "type": "send",
            "to": chat_id,
            "text": text
        }
        
        await self.ws.send(json.dumps(payload))
        return {"status": "sent"}

    async def edit_message(self, chat_id: str, message_id: str, new_content: str) -> Dict[str, Any]:
        outgoing = OutgoingMessage(chat_id=chat_id, text=new_content)
        return await self.send_message(chat_id, outgoing)

    async def set_typing_indicator(self, chat_id: str) -> None:
        pass
