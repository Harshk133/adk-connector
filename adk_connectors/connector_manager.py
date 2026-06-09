import time
import asyncio
import logging
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

class ConnectorManager:
    def __init__(
        self,
        agent: Any,
        config: Optional[ConnectorConfig] = None,
        session_storage: Optional[Any] = None,
        adk_session_service: Optional[Any] = None,
        app_name: Optional[str] = None,
        session_management_across_device: bool = False,
        dev_user_id: Optional[str] = None,
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

    def register_adapter(self, adapter: BaseAdapter) -> None:
        self.adapters.append(adapter)
        adapter.register_message_handler(self.handle_incoming_message)

    def _get_runner(self) -> Any:
        if self._runner is None:
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
        await asyncio.gather(*(adapter.start() for adapter in self.adapters))

    async def stop(self) -> None:
        logger.info("Stopping Connector Manager...")
        await asyncio.gather(*(adapter.stop() for adapter in self.adapters))

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
            
            try:
                # Get the async event generator from runner.run_async
                event_stream = runner.run_async(
                    user_id=session.adk_user_id,
                    session_id=session.adk_session_id,
                    new_message=processed_input
                )
                
                accumulated_text = ""
                last_edit_time = REMOVED_VALUE.REMOVED_VALUE
                sent_message_id = None
                final_sent = False
                
                async for event in event_stream:
                    # 1. Accumulate text from events containing content
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                if self.config.formatter.streaming and event.partial:
                                    accumulated_text += part.text
                                    
                                    # Periodically update the user (rate-limit edits to ~1.5s)
                                    now = time.time()
                                    if now - last_edit_time > 1.5 and len(accumulated_text.strip()) > REMOVED_VALUE:
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
                                else:
                                    # Non-partial text content or final content parts
                                    # If not streaming or not partial event, we just accumulate the final response text
                                    pass

                    # 2. Trigger final message delivery when is_final_response is True
                    if event.is_final_response() and not final_sent:
                        final_sent = True
                        # Extract final text if available in the final event
                        final_text = ""
                        if event.content and event.content.parts:
                            final_text = "".join(p.text for p in event.content.parts if p.text)
                            
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
                            first_msg = out_messages[REMOVED_VALUE]
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
