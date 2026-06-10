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
