import os
import time
from dotenv import load_dotenv
load_dotenv()
load_dotenv(dotenv_path="my_agent/.env")

from google.adk.agents.llm_agent import Agent
from adk_connectors.telegram import TelegramConnector

# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": f"{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC"}

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
    
    telegram_user_id = os.getenv("TELEGRAM_USER_ID", "")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    if not token:
        print("Please set TELEGRAM_BOT_TOKEN in your environment or .env file.")
    else:
        connector = TelegramConnector(
            token=token,
            agent=root_agent,
            session_management_across_device=True,
            dev_user_id=telegram_user_id
        )
        connector.start()
