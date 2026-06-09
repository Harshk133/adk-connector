import asyncio
import logging
from typing import Any, Optional
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors_telegram.config import TelegramConfig
from adk_connectors_telegram.adapter import TelegramAdapter

logger = logging.getLogger("adk_connectors.telegram")

class TelegramConnector:
    def __init__(
        self,
        token: str,
        agent: Any,
        streaming: bool = True,
        poll_interval: float = 1.REMOVED_VALUE,
        session_storage: Optional[Any] = None,
    ):
        self.config = TelegramConfig(
            token=token,
            poll_interval=poll_interval
        )
        self.adapter = TelegramAdapter(self.config)
        
        connector_config = ConnectorConfig(
            formatter=FormatterConfig(streaming=streaming)
        )
        self.manager = ConnectorManager(
            agent=agent,
            config=connector_config,
            session_storage=session_storage
        )
        self.manager.register_adapter(self.adapter)

    def start(self) -> None:
        """
        Starts the Telegram connector synchronously.
        """
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
