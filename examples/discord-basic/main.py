import os
import asyncio
import logging
from google.adk.agents import Agent
from adk_connectors import ConnectorManager, ConnectorConfig, FormatterConfig
from adk_connectors.discord import DiscordAdapter, DiscordConfig

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("discord_basic")

async def main():
    # Load settings from environment variables
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not discord_token:
        logger.error("Error: DISCORD_BOT_TOKEN environment variable is not set!")
        print("\nPlease set the DISCORD_BOT_TOKEN env variable.")
        print("You can get one from the Discord Developer Portal.")
        return

    # Check for Gemini API key and set it in the environment
    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
    else:
        logger.warning("GEMINI_API_KEY is not set. The Google ADK agent might fail if you start chatting.")

    # Initialize the Google ADK Agent
    logger.info("Initializing Google ADK Agent...")
    agent = Agent(
        name="adk_discord_assistant",
        model="gemini-2.5-flash",
        instruction="You are a helpful conversational assistant which helps users.",
    )

    # Initialize the Discord Adapter
    logger.info("Setting up Discord Adapter...")
    discord_config = DiscordConfig(
        token=discord_token
    )
    adapter = DiscordAdapter(config=discord_config)

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
            await asyncio.sleep(3600)
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
