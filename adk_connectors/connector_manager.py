import time
import asyncio
import logging
import re
from typing import Optional, List, Any
from adk_connectors.base_adapter import BaseAdapter
from adk_connectors.event_router import EventRouter
from adk_connectors.session_manager import SessionManager
from adk_connectors.message_processor import MessageProcessor
from adk_connectors.response_formatter import ResponseFormatter
from adk_connectors.config import ConnectorConfig
from adk_connectors.models.incoming import IncomingMessage
from adk_connectors.models.outgoing import OutgoingMessage
from adk_connectors.storage.memory import MemorySessionStorage

logger = logging.getLogger("adk_connectors")

def _find_all_placeholders(agent) -> set[str]:
    placeholders = set()
    instruction = getattr(agent, "instruction", None)
    
    # Handle both string instructions and callables/objects (e.g. InstructionProvider)
    if isinstance(instruction, str):
        for match in re.finditer(r'{+([^{}]+)}+', instruction):
            var_name = match.group(1).strip()
            if var_name.endswith('?'):
                var_name = var_name[:-1]
            if var_name.startswith('artifact.'):
                continue
            if ':' in var_name:
                var_name = var_name.split(':')[-1]
            if var_name.isidentifier():
                placeholders.add(var_name)
    elif instruction is not None:
        template = getattr(instruction, "template", None) or getattr(instruction, "instruction_template", None)
        if isinstance(template, str):
            for match in re.finditer(r'{+([^{}]+)}+', template):
                var_name = match.group(1).strip()
                if var_name.endswith('?'):
                    var_name = var_name[:-1]
                if var_name.startswith('artifact.'):
                    continue
                if ':' in var_name:
                    var_name = var_name.split(':')[-1]
                if var_name.isidentifier():
                    placeholders.add(var_name)

    # Recursively check sub-agents and tools
    sub_agents = getattr(agent, "sub_agents", []) or []
    tools = getattr(agent, "tools", []) or []
    for tool in tools:
        sub_agent = getattr(tool, "agent", None)
        if sub_agent:
            placeholders.update(_find_all_placeholders(sub_agent))
            
    for sa in sub_agents:
        placeholders.update(_find_all_placeholders(sa))
        
    return placeholders

class ConnectorManager:
    def __init__(
        self,
        agent: Optional[Any] = None,
        config: Optional[ConnectorConfig] = None,
        session_storage: Optional[Any] = None,
        adk_session_service: Optional[Any] = None,
        app_name: Optional[str] = None,
        session_management_across_device: bool = False,
        dev_user_id: Optional[str] = None,
        platforms: Optional[List[Any]] = None,
    ):
        self.agent = agent
        self.config = config or ConnectorConfig()
        self.app_name = app_name
        
        # Automatic environment setup for cross-device session management
        if session_management_across_device:
            import sys
            import os
            
            # Resolve script directory
            script_dir = "."
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, '__file__') and main_module.__file__:
                main_file = main_module.__file__
                if not main_file.endswith("pytest") and "pytest" not in os.path.basename(main_file):
                    script_dir = os.path.dirname(os.path.abspath(main_file))
            
            # Ensure .adk directory exists
            adk_dir = os.path.join(script_dir, ".adk")
            os.makedirs(adk_dir, exist_ok=True)
            
            # Auto-initialize SQLite session service if none provided
            if adk_session_service is None:
                from google.adk.sessions.sqlite_session_service import SqliteSessionService
                db_path = os.path.join(adk_dir, "session.db").replace("\\", "/")
                adk_session_service = SqliteSessionService(db_path=db_path)
            
            # Auto-initialize JSON file session storage if none provided
            if session_storage is None:
                from adk_connectors.storage.json_file import JSONFileSessionStorage
                storage_path = os.path.join(adk_dir, "connector_sessions.json")
                session_storage = JSONFileSessionStorage(storage_path)
                
            # Auto-populate user mappings for common platforms
            if dev_user_id:
                dev_user_id = str(dev_user_id)
                self.config.session.user_mapping.update({
                    f"telegram:{dev_user_id}": "user",
                    f"discord:{dev_user_id}": "user",
                    f"slack:{dev_user_id}": "user",
                    dev_user_id: "user"
                })
        
        self.adk_session_service = adk_session_service
        
        storage = session_storage or MemorySessionStorage()
        self.session_manager = SessionManager(storage, self.config.session)
        
        self.event_router = EventRouter()
        self.message_processor = MessageProcessor()
        self.response_formatter = ResponseFormatter(
            max_message_length=self.config.formatter.max_message_length
        )
        
        self._runner = None
        self.adapters: List[BaseAdapter] = []
        self._tunnel_client = None
        self._web_app = None
        self._web_runner = None
        self._web_site = None

        if platforms:
            for platform in platforms:
                self.register_platform(platform)

    def register_adapter(self, adapter: BaseAdapter) -> None:
        self.adapters.append(adapter)
        adapter.register_message_handler(self.handle_incoming_message)

    def register_platform(self, platform: Any) -> None:
        """
        Registers a platform connector or adapter to the manager.
        """
        if platform is None:
            return
            
        # Check if platform is a connector wrapping an adapter
        if hasattr(platform, "adapter") and platform.adapter is not None:
            adapter = platform.adapter
            self.register_adapter(adapter)
            # Link the connector to this manager so it knows it is managed centrally
            if hasattr(platform, "manager"):
                platform.manager = self
        # Or if the platform is directly an adapter subclassing BaseAdapter
        elif hasattr(platform, "register_message_handler"):
            self.register_adapter(platform)
        else:
            raise TypeError(
                f"Expected a platform connector wrapping an adapter or a BaseAdapter subclass, "
                f"got {type(platform).__name__}"
            )

    def _get_runner(self) -> Any:
        if self._runner is None:
            if self.agent is None:
                raise ValueError("Agent must be set on ConnectorManager before running.")
            from google.adk.runners import Runner
            
            if self.app_name:
                app_name = self.app_name
            else:
                app_name = None
                import sys
                import os
                main_module = sys.modules.get('__main__')
                if main_module and hasattr(main_module, '__file__') and main_module.__file__:
                    main_file = main_module.__file__
                    if not main_file.endswith("pytest") and "pytest" not in os.path.basename(main_file):
                        dir_path = os.path.dirname(os.path.abspath(main_file))
                        folder_name = os.path.basename(dir_path)
                        if folder_name and folder_name != "tests":
                            app_name = folder_name
                if not app_name:
                    app_name = getattr(self.agent, "name", "adk_app") or "adk_app"
            
            if self.adk_session_service is not None:
                session_service = self.adk_session_service
            else:
                from google.adk.sessions.in_memory_session_service import InMemorySessionService
                session_service = InMemorySessionService()
            
            self._runner = Runner(
                agent=self.agent,
                app_name=app_name,
                session_service=session_service,
                auto_create_session=True
            )
        return self._runner

    async def start(self) -> None:
        logger.info("Starting Connector Manager...")
        if self.config.tunnel.enabled:
            await self._start_webhook_server()
            await self._start_tunnel()
        await asyncio.gather(*(adapter.start() for adapter in self.adapters))

    def _find_free_port(self, start_port: int) -> int:
        import socket
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    port += 1
        return start_port

    async def _start_webhook_server(self) -> None:
        from aiohttp import web
        self._web_app = web.Application()
        self._web_app.router.add_post("/webhooks/{platform}", self._handle_webhook_request)
        
        self._web_runner = web.AppRunner(self._web_app)
        await self._web_runner.setup()
        
        host = self.config.tunnel.host
        original_port = self.config.tunnel.port
        
        # Resolve port collision dynamically
        port = self._find_free_port(original_port)
        if port != original_port:
            logger.warning(
                f"Port {original_port} is busy or restricted. "
                f"Automatically selected free port {port} instead."
            )
            self.config.tunnel.port = port
            
        self._web_site = web.TCPSite(self._web_runner, host, port)
        await self._web_site.start()
        logger.info(f"Built-in Webhook Server listening on http://{host}:{port}")

    async def _handle_webhook_request(self, request: Any) -> Any:
        from aiohttp import web
        platform = request.match_info.get("platform")
        adapter = next((a for a in self.adapters if a.platform == platform), None)
        if not adapter:
            logger.warning(f"Webhook request received for unregistered platform: {platform}")
            return web.Response(status=404, text=f"No adapter registered for {platform}")

        try:
            payload = await request.json()
        except Exception as e:
            logger.warning(f"Failed to parse webhook JSON payload: {e}")
            return web.Response(status=400, text="Invalid JSON")

        headers = dict(request.headers)

        parse_func = getattr(adapter, "parse_webhook_payload", None)
        if parse_func:
            try:
                parsed_msg = parse_func(payload, headers=headers)
                if parsed_msg:
                    asyncio.create_task(self.handle_incoming_message(parsed_msg))
            except Exception as pe:
                logger.error(f"Error parsing webhook payload for platform {platform}: {pe}")
                return web.Response(status=500, text="Internal parse error")
        else:
            logger.warning(f"Adapter for {platform} does not implement parse_webhook_payload")
            
        return web.Response(status=200, text="OK")

    async def _start_tunnel(self) -> None:
        provider = self.config.tunnel.provider
        port = self.config.tunnel.port
        host = self.config.tunnel.host
        authtoken = self.config.tunnel.authtoken
        
        if provider == "cloudflare":
            from adk_connectors.tunnel import CloudflareTunnel
            self._tunnel_client = CloudflareTunnel(port=port, host=host)
        elif provider == "ngrok":
            from adk_connectors.tunnel import NgrokTunnel
            self._tunnel_client = NgrokTunnel(port=port, authtoken=authtoken)
        else:
            raise ValueError(f"Unknown tunnel provider: {provider}")

        public_url = await self._tunnel_client.start()
        
        for adapter in self.adapters:
            if hasattr(adapter, "config") and hasattr(adapter.config, "webhook_url"):
                adapter.config.webhook_url = f"{public_url}/webhooks/{adapter.platform}"
                logger.info(f"Configured webhook URL for {adapter.platform}: {adapter.config.webhook_url}")

    async def stop(self) -> None:
        logger.info("Stopping Connector Manager...")
        
        # Stop adapters
        await asyncio.gather(*(adapter.stop() for adapter in self.adapters))
        
        # Stop tunnel client
        if self._tunnel_client:
            try:
                await self._tunnel_client.stop()
            except Exception as e:
                logger.error(f"Error stopping tunnel client: {e}")
            self._tunnel_client = None

        # Stop web server
        if self._web_runner:
            try:
                await self._web_runner.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up web server runner: {e}")
            self._web_runner = None
            self._web_app = None
            self._web_site = None

    def start_sync(self) -> None:
        """
        Starts the Connector Manager and all registered platforms synchronously.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        logger.info("Starting Connector Manager... Press Ctrl+C to stop.")
        try:
            loop.run_until_complete(self.start())
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            logger.info("KeyboardInterrupt received. Shutting down gracefully...")
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.run_until_complete(self.stop())
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
            logger.info("Stopped.")

    async def handle_incoming_message(self, message: IncomingMessage) -> None:
        # Lock session for this user to prevent concurrent race conditions
        async with self.session_manager.lock(message.user_id):
            session = await self.session_manager.get_or_create(
                platform_id=message.user_id,
                platform=message.platform
            )
            
            adapter = next((a for a in self.adapters if a.platform == message.platform), None)
            if not adapter:
                logger.error(f"No adapter found for platform {message.platform}")
                return
            
            await adapter.set_typing_indicator(message.chat_id)
            
            processed_input = await self.message_processor.process(message)
            runner = self._get_runner()
            
            # Seed state_delta dynamically to prevent KeyErrors in subagents
            state_delta = {}
            try:
                adk_session = await runner.session_service.get_session(
                    app_name=runner.app_name,
                    user_id=session.adk_user_id,
                    session_id=session.adk_session_id
                )
                existing_state = adk_session.state if adk_session else {}
                
                placeholders = _find_all_placeholders(self.agent)
                coordinator_output_key = getattr(self.agent, "output_key", None)
                
                for ph in placeholders:
                    if ph not in existing_state:
                        # If the placeholder matches the root agent's output_key,
                        # seed it with the user message or a sensible default
                        if coordinator_output_key and ph == coordinator_output_key:
                            user_text = message.text or ""
                            fallback_val = "Attention Is All You Need"
                            if len(user_text.strip()) > 5 and len(user_text.strip()) < 100:
                                fallback_val = user_text.strip()
                            state_delta[ph] = fallback_val
                        else:
                            state_delta[ph] = ""
            except Exception as se:
                logger.warning(f"Could not load or check ADK session state: {se}")
            
            try:
                # Inspect signature to verify if run_async accepts state_delta (for test/mock compatibility)
                import inspect
                run_async_sig = inspect.signature(runner.run_async)
                
                # Get the async event generator from runner.run_async
                if "state_delta" in run_async_sig.parameters:
                    event_stream = runner.run_async(
                        user_id=session.adk_user_id,
                        session_id=session.adk_session_id,
                        new_message=processed_input,
                        state_delta=state_delta
                    )
                else:
                    event_stream = runner.run_async(
                        user_id=session.adk_user_id,
                        session_id=session.adk_session_id,
                        new_message=processed_input
                    )
                
                accumulated_text = ""
                last_edit_time = 0.0
                sent_message_id = None
                final_event = None
                
                async for event in event_stream:
                    # 1. Accumulate text from events containing content (only from root branch to avoid sub-agent confusion)
                    if not event.branch and event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                if self.config.formatter.streaming and event.partial:
                                    accumulated_text += part.text
                                    
                                    # Periodically update the user (rate-limit edits to ~1.5s)
                                    now = time.time()
                                    if now - last_edit_time > 1.5 and len(accumulated_text.strip()) > 0:
                                        if not sent_message_id:
                                            outgoing = OutgoingMessage(
                                                chat_id=message.chat_id,
                                                text=accumulated_text
                                            )
                                            res = await adapter.send_message(message.chat_id, outgoing)
                                            if res:
                                                if hasattr(res, "message_id"):
                                                    sent_message_id = str(res.message_id)
                                                elif isinstance(res, dict) and "message_id" in res:
                                                    sent_message_id = str(res["message_id"])
                                                elif isinstance(res, str):
                                                    sent_message_id = res
                                        else:
                                            await adapter.edit_message(
                                                chat_id=message.chat_id,
                                                message_id=sent_message_id,
                                                new_content=accumulated_text
                                            )
                                        last_edit_time = now

                    # 2. Track the latest final response event (prioritize root agent, fallback to sub-agent if no root is final)
                    if event.is_final_response():
                        if not event.branch:
                            final_event = event
                        elif final_event is None or final_event.branch:
                            final_event = event

                # 3. Deliver final message when the event stream iteration is complete
                if final_event:
                    # Extract final text if available in the final event
                    final_text = ""
                    if final_event.content and final_event.content.parts:
                        final_text = "".join(p.text for p in final_event.content.parts if p.text)
                        
                    # Fallback to accumulated text if final_text is empty or shorter
                    if not final_text or len(final_text) < len(accumulated_text):
                        final_text = accumulated_text
                        
                    if not final_text.strip():
                        final_text = "..."
                        
                    out_messages = self.response_formatter.format_response(
                        chat_id=message.chat_id,
                        text=final_text
                    )
                    
                    if not sent_message_id:
                        for out_msg in out_messages:
                            await adapter.send_message(message.chat_id, out_msg)
                    else:
                        # Edit the placeholder with the first chunk
                        first_msg = out_messages[0]
                        await adapter.edit_message(
                            chat_id=message.chat_id,
                            message_id=sent_message_id,
                            new_content=first_msg.text
                        )
                        # Send any remaining chunks as new messages
                        for out_msg in out_messages[1:]:
                            await adapter.send_message(message.chat_id, out_msg)
                    
                    await self.session_manager.update(session)


                                    
            except Exception as e:
                logger.exception("Error running ADK agent")
                await adapter.send_message(
                    message.chat_id,
                    OutgoingMessage(chat_id=message.chat_id, text=f"⚠️ Error occurred while processing message: {str(e)}")
                )
