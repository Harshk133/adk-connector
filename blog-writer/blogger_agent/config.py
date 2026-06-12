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

import os
from dataclasses import dataclass
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

import google.auth

# To use AI Studio credentials:
# 1. Create a .env file in the /app directory with:
#    GOOGLE_GENAI_USE_VERTEXAI=FALSE
#    GOOGLE_API_KEY=PASTE_YOUR_ACTUAL_API_KEY_HERE
# 2. This will override the default Vertex AI configuration
# _, project_id = google.auth.default()
# os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
# os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
# os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")


@dataclass
class ResearchConfiguration:
    """Configuration for research-related models and parameters.

    Attributes:
        critic_model (str): Model for evaluation tasks.
        worker_model (str): Model for working/generation tasks.
        max_search_iterations (int): Maximum search iterations allowed.
    """

    critic_model: str = "litellm:openrouter/google/gemini-2.5-flash-lite"
    worker_model: str = "litellm:openrouter/google/gemini-2.5-flash-lite"
    max_search_iterations: int = 2
    token: str = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_user_id: str = os.getenv("TELEGRAM_USER_ID")
    discord_token: str = os.getenv("DISCORD_BOT_TOKEN")
    discord_user_id: str = os.getenv("DISCORD_USER_ID")
    whatsapp_port: int = int(os.getenv("WHATSAPP_PORT", "3001"))
    whatsapp_host: str = os.getenv("WHATSAPP_HOST", "127.0.0.1")
    whatsapp_bridge_token: str = os.getenv("WHATSAPP_BRIDGE_TOKEN")


config = ResearchConfiguration()
