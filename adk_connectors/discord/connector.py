import asyncio
import logging
from typing import Any, Optional
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors.discord.config import DiscordConfig
from adk_connectors.discord.adapter import DiscordAdapter

logger = logging.getLogger("adk_connectors.discord")

class DiscordConnector:
    def __init__(
        self,
        token: str,
        agent: Any,
        streaming: bool = True,
        session_storage: Optional[Any] = None,
        adk_session_service: Optional[Any] = None,
        connector_config: Optional[ConnectorConfig] = None,
        app_name: Optional[str] = None,
        session_management_across_device: bool = False,
        dev_user_id: Optional[str] = None,
    ):
        self.config = DiscordConfig(
            token=token
        )
        self.adapter = DiscordAdapter(self.config)
        
        if connector_config is None:
            connector_config = ConnectorConfig(
                formatter=FormatterConfig(streaming=streaming)
            )
        self.manager = ConnectorManager(
            agent=agent,
            config=connector_config,
            session_storage=session_storage,
            adk_session_service=adk_session_service,
            app_name=app_name,
            session_management_across_device=session_management_across_device,
            dev_user_id=dev_user_id
        )
        self.manager.register_adapter(self.adapter)

    def start(self) -> None:
        """
        Starts the Discord connector synchronously.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        logger.info("Starting Discord Bot... Press Ctrl+C to stop.")
        try:
            loop.run_until_complete(self.manager.start())
            # Keep the loop running
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
                loop.run_until_complete(self.manager.stop())
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
            logger.info("Stopped.")
