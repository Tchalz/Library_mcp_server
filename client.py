"""
Library Server — MCP client.

Connects to app.py over stdio (spawning it as a subprocess, the standard
way local MCP servers are launched) using the OpenAI Agents SDK, then hands
it a natural-language request that requires chaining two tool calls in one
conversation: search_books to find a book, then borrow_book to check it
out.

This client is wired to run against OpenRouter's free tier (same as the
Tchalz project) rather than OpenAI directly, so it reuses an existing
API_TOKEN instead of requiring a paid OpenAI key. The OpenAI Agents SDK
talks to OpenAI's Responses API by default; OpenRouter only supports the
older Chat Completions API, so both the client and the API mode are
overridden below before any Agent is created.

Requires an API_TOKEN in the environment (or a .env file, since
python-dotenv is loaded below) — get one at https://openrouter.ai/keys.

Run:
    python client.py
"""

import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

load_dotenv()

# A free, tool-calling-capable OpenRouter model. Check openrouter.ai/models
# (filtered to price = $0) if this ID has rotated out by the time you run this.
MODEL_NAME = "openrouter/free"


def build_openrouter_model() -> OpenAIChatCompletionsModel:
    """
    Builds an explicit model object pointed at OpenRouter.

    Passing a bare string like "qwen/qwen3-coder:free" as Agent(model=...)
    doesn't work here: the Agents SDK's default MultiProvider interprets
    the text before the "/" as a *provider prefix* (e.g. "litellm/gpt-4"),
    not as part of an OpenRouter model ID, and raises "Unknown prefix: qwen".
    Wrapping it in OpenAIChatCompletionsModel with our own OpenRouter-backed
    AsyncOpenAI client sidesteps that resolution logic entirely.
    """
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        raise SystemExit(
            "API_TOKEN is not set. Add it to a .env file (get a free key at "
            "https://openrouter.ai/keys) before running this client."
        )

    client = AsyncOpenAI(api_key=api_token, base_url="https://openrouter.ai/api/v1")
    return OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)


async def main() -> None:
    set_tracing_disabled(True)  # tracing would otherwise try to phone home to platform.openai.com using a real OPENAI_API_KEY we don't have
    model = build_openrouter_model()

    async with MCPServerStdio(
        name="Library Server",
        params={
            "command": "python",
            "args": ["app.py"],
        },
    ) as library_server:

        agent = Agent(
            name="Librarian",
            model=model,
            instructions=(
                "You are a helpful library assistant. Use the available "
                "tools to search the catalog, check availability, and "
                "borrow or return books on behalf of members. Always "
                "check availability before borrowing if you're not already "
                "sure a copy is free, and report tool errors back to the "
                "user in plain language instead of retrying blindly."
            ),
            mcp_servers=[library_server],
        )

        user_request = (
            "Find me books about space, then borrow one for member M001."
        )
        print(f"User: {user_request}\n")

        result = await Runner.run(agent, user_request)

        print("--- Tool calls made this run ---")
        tool_call_count = 0
        for item in result.new_items:
            if item.type == "tool_call_item":
                tool_call_count += 1
                print(f"  [{tool_call_count}] {item.tool_name}")
            elif item.type == "tool_call_output_item":
                print(f"      -> {item.output}")

        print(f"\nTotal tool calls: {tool_call_count}")

        print("\n--- Final agent response ---")
        print(result.final_output)

        assert tool_call_count >= 2, "Expected at least two tool calls in this conversation."


if __name__ == "__main__":
    asyncio.run(main())
