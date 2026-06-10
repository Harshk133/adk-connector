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

"""Academic_newresearch_agent for finding new research lines"""

from google.adk import Agent

from . import prompt

import os
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_key:
    from google.adk.models.lite_llm import LiteLlm
    MODEL = LiteLlm(model="openrouter/google/gemini-2.5-flash-lite")
else:
    MODEL = "gemini-2.5-pro"

academic_newresearch_agent = Agent(
    model=MODEL,
    name="academic_newresearch_agent",
    instruction=prompt.ACADEMIC_NEWRESEARCH_PROMPT,
)
