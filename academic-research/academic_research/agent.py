# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Academic_Research: Research advice, related literature finding, research area proposals, web knowledge access."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.academic_newresearch import academic_newresearch_agent
from .sub_agents.academic_websearch import academic_websearch_agent

import os
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    from google.adk.models.lite_llm import LiteLlm
    MODEL = LiteLlm(model="openrouter/google/gemini-2.5-flash-lite")
else:
    MODEL = "gemini-2.5-flash"


academic_coordinator = LlmAgent(
    name="academic_coordinator",
    model=MODEL,
    description=(
        "analyzing seminal papers provided by the users, "
        "providing research advice, locating current papers "
        "relevant to the seminal paper, generating suggestions "
        "for new research directions, and accessing web resources "
        "to acquire knowledge"
    ),
    instruction=prompt.ACADEMIC_COORDINATOR_PROMPT,
    output_key="seminal_paper",
    tools=[
        AgentTool(agent=academic_websearch_agent),
        AgentTool(agent=academic_newresearch_agent),
    ],
)

root_agent = academic_coordinator


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    import logging
    from dotenv import load_dotenv
    from adk_connectors.telegram import TelegramConnector
    
    # Load environment variables
    load_dotenv()
    load_dotenv(dotenv_path=".env")
    load_dotenv(dotenv_path="../my_agent/.env")
    
    # Ensure GEMINI_API_KEY is populated if GOOGLE_API_KEY is available
    if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")
        
    # Configure logging to see polling and events in the console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_user_id = os.getenv("TELEGRAM_USER_ID")
    
    if not token:
        print("\n❌ Error: TELEGRAM_BOT_TOKEN not found in environment or .env file.")
        print("Please configure your .env file with your Telegram Bot Token and Gemini API Key.\n")
    else:
        print(f"🚀 Starting Telegram Connector for agent '{root_agent.name}'...")
        print(f"🔄 Cross-device session sync: ENABLED (User ID mapping: {telegram_user_id})")
        
        connector = TelegramConnector(
            token=token,
            agent=root_agent,
            session_management_across_device=True,
            dev_user_id=telegram_user_id
        )
        connector.start()
