"""
Library Server — MCP client (Streamlit UI).

Connects to app.py over Streamable HTTP (http://localhost:8001/mcp) using
the OpenAI Agents SDK, and exposes a chat interface where the user can ask
the librarian agent to search, check availability, borrow, or return books.

This client is wired to run against OpenRouter's free tier (same as the
Tchalz project) rather than OpenAI directly, so it reuses an existing
API_TOKEN instead of requiring a paid OpenAI key. The OpenAI Agents SDK
talks to OpenAI's Responses API by default; OpenRouter only supports the
older Chat Completions API, so both the client and the API mode are
overridden below before any Agent is created.

Requires:
  - An API_TOKEN in the environment (or a .env file, since python-dotenv
    is loaded below) — get one at https://openrouter.ai/keys.
  - The MCP server (app.py) already running and listening on
    http://localhost:8001/mcp — start it in a separate terminal with
    `python app.py` before launching this app.

Run:
    streamlit run client.py
"""

import asyncio
import os

import streamlit as st
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

load_dotenv()

# A free, tool-calling-capable OpenRouter model. Check openrouter.ai/models
# (filtered to price = $0) if this ID has rotated out by the time you run this.
MODEL_NAME = "openai/gpt-oss-20b:free"

st.set_page_config(page_title="Library Assistant", page_icon="📚")
set_tracing_disabled(True)  # tracing would otherwise try to phone home to platform.openai.com using a real OPENAI_API_KEY we don't have


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
        st.error(
            "API_TOKEN is not set. Add it to a .env file (get a free key at "
            "https://openrouter.ai/keys) before running this app."
        )
        st.stop()

    client = AsyncOpenAI(api_key=api_token, base_url="https://openrouter.ai/api/v1")
    return OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)


async def run_librarian(user_request: str):
    """Spins up a fresh MCP connection + agent, runs one turn, returns the result."""
    model = build_openrouter_model()

    async with MCPServerStreamableHttp(
        name="Library Server",
        params={"url": "http://localhost:8001/mcp"},
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
                "user in plain language instead of retrying blindly. "
                "This is a non-interactive session, so if the user's request "
                "is ambiguous (e.g. which specific book to borrow), make a "
                "reasonable choice yourself using an available copy rather "
                "than asking a follow-up question."
            ),
            mcp_servers=[library_server],
        )

        result = await Runner.run(agent, user_request)

        tool_calls = []
        for item in result.new_items:
            if item.type == "tool_call_item":
                tool_calls.append({"name": item.tool_name, "output": None})
            elif item.type == "tool_call_output_item":
                if tool_calls:
                    tool_calls[-1]["output"] = item.output

        return result.final_output, tool_calls


def render_tool_calls(tool_calls):
    if not tool_calls:
        return
    with st.expander(f"🔧 Tool calls made ({len(tool_calls)})"):
        for i, call in enumerate(tool_calls, start=1):
            st.markdown(f"**[{i}] {call['name']}**")
            output = call["output"]
            if isinstance(output, dict) and "text" in output:
                st.text(output["text"])
            else:
                st.text(str(output))


st.title("📚 Library Assistant")
st.caption("Ask me to search for books, check availability, or borrow/return them on behalf of a member.")

if "messages" not in st.session_state:
    st.session_state.messages = []  # each item: {"role": ..., "content": ..., "tool_calls": [...] (optional)}

# Replay chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            render_tool_calls(msg["tool_calls"])

user_request = st.chat_input("e.g. Find me books about space, then borrow one for member M001.")

if user_request:
    st.session_state.messages.append({"role": "user", "content": user_request})
    with st.chat_message("user"):
        st.markdown(user_request)

    with st.chat_message("assistant"):
        with st.spinner("Working on it..."):
            try:
                final_output, tool_calls = asyncio.run(run_librarian(user_request))
            except Exception as exc:  # noqa: BLE001 — surface any failure to the UI instead of crashing
                final_output = f"⚠️ Something went wrong: {exc}"
                tool_calls = []

        st.markdown(final_output)
        render_tool_calls(tool_calls)

    st.session_state.messages.append(
        {"role": "assistant", "content": final_output, "tool_calls": tool_calls}
    )
