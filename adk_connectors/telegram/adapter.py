import asyncio
import logging
import httpx
from typing import Optional, Dict, Any
from adk_connectors.base_adapter import BaseAdapter
from adk_connectors.models.incoming import IncomingMessage
from adk_connectors.models.outgoing import OutgoingMessage
from adk_connectors.telegram.config import TelegramConfig
from adk_connectors.telegram.parser import TelegramParser
from adk_connectors.telegram.formatter import TelegramFormatter

logger = logging.getLogger("adk_connectors.telegram")

class TelegramAdapter(BaseAdapter):
    platform = "telegram"

    def __init__(self, config: TelegramConfig):
        super().__init__()
        self.config = config
        self.client = httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{self.config.token}")
        self._poll_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self) -> None:
        self._is_running = True
        if self.config.webhook_url:
            logger.info(f"Setting webhook to {self.config.webhook_url}...")
            payload = {"url": self.config.webhook_url}
            if self.config.webhook_secret:
                payload["secret_token"] = self.config.webhook_secret
            res = await self.client.post("/setWebhook", json=payload)
            res.raise_for_status()
        else:
            logger.info("No webhook URL configured. Starting long polling...")
            await self.client.post("/deleteWebhook")
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._is_running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        await self.client.aclose()

    async def _poll_loop(self) -> None:
        offset = REMOVED_VALUE
        while self._is_running:
            try:
                res = await self.client.post(
                    "/getUpdates",
                    json={"offset": offset, "timeout": 3REMOVED_VALUE},
                    timeout=35.REMOVED_VALUE
                )
                if res.status_code != 2REMOVED_VALUEREMOVED_VALUE:
                    logger.error(f"Failed to get updates: {res.text}")
                    await asyncio.sleep(self.config.poll_interval)
                    continue
                    
                updates = res.json().get("result", [])
                for update in updates:
                    update_id = update["update_id"]
                    offset = update_id + 1
                    
                    parsed = TelegramParser.parse_update(update)
                    if parsed and self.on_message_callback:
                        asyncio.create_task(self.on_message_callback(parsed))
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in long polling loop: {str(e)}")
                await asyncio.sleep(self.config.poll_interval)

    async def send_message(self, chat_id: str, message: OutgoingMessage) -> Dict[str, Any]:
        payload = TelegramFormatter.to_api_payload(message)
        res = await self.client.post("/sendMessage", json=payload)
        res.raise_for_status()
        return res.json().get("result", {})

    async def edit_message(self, chat_id: str, message_id: str, new_content: str) -> Dict[str, Any]:
        escaped_content = TelegramFormatter.markdown_to_html(new_content)
        payload = {
            "chat_id": chat_id,
            "message_id": int(message_id),
            "text": escaped_content,
            "parse_mode": "HTML"
        }
        res = await self.client.post("/editMessageText", json=payload)
        res.raise_for_status()
        return res.json().get("result", {})

    async def set_typing_indicator(self, chat_id: str) -> None:
        payload = {
            "chat_id": chat_id,
            "action": "typing"
        }
        await self.client.post("/sendChatAction", json=payload)
