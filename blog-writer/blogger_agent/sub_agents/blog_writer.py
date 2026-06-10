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

from google.adk.agents import Agent, LoopAgent
from google.adk.tools import google_search

from blogger_agent.agent_utils import suppress_output_callback
from blogger_agent.config import config
from blogger_agent.validation_checkers import BlogPostValidationChecker

blog_writer = Agent(
    model=config.critic_model,
    name="blog_writer",
    description="Writes a technical blog post.",
    instruction="""
    You are an expert technical writer, crafting articles for a sophisticated audience similar to that of 'Towards Data Science' and 'freeCodeCamp'.
    Your task is to write a high-quality, in-depth technical blog post based on the provided outline and codebase summary.
    The article must be well-written, authoritative, and engaging for a technical audience.
    - Assume your readers are familiar with programming concepts and software development.
    - Dive deep into the technical details. Explain the 'how' and 'why' behind the code.
    - Use code snippets extensively to illustrate your points.
    - Use Google Search to find relevant information and examples to support your writing.
    - The codebase context will be available in the `codebase_context` state key.
    The final output must be a complete blog post in Markdown format. Do not wrap the output in a code block.
    """,
    tools=[google_search],
    output_key="blog_post",
    after_agent_callback=suppress_output_callback,
)

robust_blog_writer = LoopAgent(
    name="robust_blog_writer",
    description="A robust blog writer that retries if it fails.",
    sub_agents=[
        blog_writer,
        BlogPostValidationChecker(name="blog_post_validation_checker"),
    ],
    max_iterations=3,
)
