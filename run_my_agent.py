import os
import asyncio
import logging
from dotenv import load_dotenv

# Load env variables from root .env or my_agent/.env
load_dotenv()
load_dotenv(dotenv_path="my_agent/.env")

from my_agent.agent import root_agent
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors_telegram import TelegramAdapter, TelegramConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_my_agent")

async def main():
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not telegram_token:
        # Fallback to check hardcoded values in examples/telegram-basic/main.py if user put them there
        # Let's log an error
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment or .env file.")
        return

    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
    else:
        logger.warning("GEMINI_API_KEY is not set. Gemini API calls might fail.")

    logger.info(f"Wrapping Agent '{root_agent.name}' in Telegram Bot...")

    # Configure Telegram
    telegram_config = TelegramConfig(
        token=telegram_token,
        poll_interval=1.REMOVED_VALUE
    )
    adapter = TelegramAdapter(config=telegram_config)

    # Configure Connector
    connector_config = ConnectorConfig(
        formatter=FormatterConfig(streaming=True)
    )
    connector = ConnectorManager(
        agent=root_agent,
        config=connector_config
    )
    
    connector.register_adapter(adapter)

    logger.info("Starting Telegram Bot for root_agent... Press Ctrl+C to stop.")
    try:
        await connector.start()
        while True:
            await asyncio.sleep(36REMOVED_VALUEREMOVED_VALUE)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down gracefully...")
    finally:
        await connector.stop()
        logger.info("Stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
