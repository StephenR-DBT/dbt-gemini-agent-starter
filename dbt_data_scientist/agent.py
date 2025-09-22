import os, json, subprocess
from typing import Dict, List
from dotenv import load_dotenv

# ADK imports
from google.adk import Agent
from google.adk.tools import FunctionTool
# Use any LLM Provider
from google.adk.models.lite_llm import LiteLlm

# Local Imports
from . import prompts
from .tools import (
    dbt_compile,
    dbt_mcp_toolset
)
from .sub_agents import (
    dbt_model_analyzer_agent
)

# ------------- The Agent -------------
root_agent = Agent(
    name="dbt_data_scientist",
    model="gemini-2.0-flash",   # fast; use 2.0-pro for deeper analysis
    description=(
        "Agent to assist with dbt pipelines."
    ),
    instruction=prompts.ROOT_AGENT_INSTR,
    sub_agents=[dbt_model_analyzer_agent],
    tools=[dbt_compile, dbt_mcp_toolset]
)

# # --- Example Agent using OpenAI's GPT-4o ---
# # (Requires OPENAI_API_KEY)
# agent_openai = LlmAgent(
#     model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
#     name="openai_agent",
#     instruction="You are a helpful assistant powered by GPT-4o.",
#     # ... other agent parameters
# )

# # --- Example Agent using Anthropic's Claude Haiku (non-Vertex) ---
# # (Requires ANTHROPIC_API_KEY)
# agent_claude_direct = LlmAgent(
#     model=LiteLlm(model="anthropic/claude-3-haiku-20240307"),
#     name="claude_direct_agent",
#     instruction="You are an assistant powered by Claude Haiku.",
#     # ... other agent parameters
# )
