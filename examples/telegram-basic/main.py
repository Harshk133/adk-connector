import os
import asyncio
import logging
from google.adk.agents import Agent
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors_telegram import TelegramAdapter, TelegramConfig

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("telegram_basic")

async def main():
    # Load settings from environment variables
    # telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_token = "REMOVED_VALUE"
    gemini_api_key = "REMOVED_VALUE"
    
    if not telegram_token:
        logger.error("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("\nPlease set the TELEGRAM_BOT_TOKEN env variable.")
        print("You can get one by messaging @BotFather on Telegram.")
        return

    # Check for Gemini API key and set it in the environment
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
    else:
        logger.warning("GEMINI_API_KEY is not set. The Google ADK agent might fail if you start chatting.")

    # Initialize the Google ADK Agent
    logger.info("Initializing Google ADK Agent...")
    agent = Agent(
        name="adk_telegram_assistant",
        model="gemini-2.5-flash",
        instruction="You are a helpful conversational assistant which helps to tell user whats the current time in a specified city.",
    )

    # Initialize the Telegram Adapter
    logger.info("Setting up Telegram Adapter...")
    telegram_config = TelegramConfig(
        token=telegram_token,
        poll_interval=1.REMOVED_VALUE
    )
    adapter = TelegramAdapter(config=telegram_config)

    # Initialize the Connector Manager
    logger.info("Setting up ADK Connector Manager...")
    connector_config = ConnectorConfig(
        formatter=FormatterConfig(streaming=True)
    )
    connector = ConnectorManager(
        agent=agent,
        config=connector_config
    )
    
    # Register the adapter
    connector.register_adapter(adapter)

    # Start the connector manager
    logger.info("Starting connector... Press Ctrl+C to exit.")
    try:
        await connector.start()
        # Keep running
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
