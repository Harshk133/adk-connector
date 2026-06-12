import asyncio
import logging
from typing import Any, Optional
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors.telegram.config import TelegramConfig
from adk_connectors.telegram.adapter import TelegramAdapter

logger = logging.getLogger("adk_connectors.telegram")

class TelegramConnector:
    def __init__(
        self,
        token: str,
        agent: Optional[Any] = None,
        streaming: bool = True,
        poll_interval: float = 1.0,
        session_storage: Optional[Any] = None,
        adk_session_service: Optional[Any] = None,
        connector_config: Optional[ConnectorConfig] = None,
        app_name: Optional[str] = None,
        session_management_across_device: bool = False,
        dev_user_id: Optional[str] = None,
        tunnel: bool = False,
        webhook_secret: Optional[str] = None,
    ):
        self.config = TelegramConfig(
            token=token,
            poll_interval=poll_interval,
            webhook_secret=webhook_secret
        )
        self.adapter = TelegramAdapter(self.config)
        
        if connector_config is None:
            connector_config = ConnectorConfig(
                formatter=FormatterConfig(streaming=streaming)
            )
        if tunnel:
            connector_config.tunnel.enabled = True

        if agent is not None:
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
        else:
            self.manager = None

    def start(self) -> None:
        """
        Starts the Telegram connector synchronously.
        """
        if self.manager is None:
            raise ValueError(
                "Cannot start connector directly because no agent was provided during initialization. "
                "Pass this connector to a central ConnectorManager instead."
            )
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        logger.info("Starting Telegram Bot... Press Ctrl+C to stop.")
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
