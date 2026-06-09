import os
from dotenv import load_dotenv
load_dotenv()
load_dotenv(dotenv_path="my_agent/.env")

from google.adk.agents.llm_agent import Agent
from adk_connectors.telegram import TelegramConnector

# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "REMOVED_VALUE8:3REMOVED_VALUE AM"}

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
    tools=[get_current_time],
)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    token = "REMOVED_VALUE"
    if not token:
        print("Please set TELEGRAM_BOT_TOKEN in your environment or .env file.")
    else:
        connector = TelegramConnector(
            token=token,
            agent=root_agent
        )
        connector.start()
