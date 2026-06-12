import asyncio
import logging
from typing import Any, Optional
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors.whatsapp.config import WhatsAppConfig
from adk_connectors.whatsapp.adapter import WhatsAppAdapter

logger = logging.getLogger("adk_connectors.whatsapp")

class WhatsAppConnector:
    def __init__(
        self,
        agent: Optional[Any] = None,
        port: int = 3001,
        host: str = "127.0.0.1",
        bridge_token: Optional[str] = None,
        auth_dir: Optional[str] = None,
        db_path: Optional[str] = None, # ignored, for backwards compatibility
        session_storage: Optional[Any] = None,
        adk_session_service: Optional[Any] = None,
        connector_config: Optional[ConnectorConfig] = None,
        app_name: Optional[str] = None,
        session_management_across_device: bool = False,
        dev_user_id: Optional[str] = None,
    ):
        self.config = WhatsAppConfig(
            port=port,
            host=host,
            bridge_token=bridge_token,
            auth_dir=auth_dir
        )
        self.adapter = WhatsAppAdapter(self.config)
        
        if connector_config is None:
            connector_config = ConnectorConfig(
                formatter=FormatterConfig(streaming=False)
            )
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
        Starts the WhatsApp connector process synchronously.
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
        
        logger.info("Starting WhatsApp Bot... Press Ctrl+C to stop.")
        try:
            loop.run_until_complete(self.manager.start())
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


# Alias for compatibility with older code/runners
WhatsAppWebConnector = WhatsAppConnector
