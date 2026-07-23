"""
Library Assistant — Streamlit UI

Wraps the same OpenAI Agents SDK + MCP client setup from client.py in a
chat interface. Each turn spawns a fresh MCP server subprocess (app.py)
over stdio and calls Runner.run with the full prior conversation, so
context (including earlier tool results) carries across turns even
though the server process itself doesn't persist between messages.

Requires an API_TOKEN in the environment or a .env file — get one at
https://openrouter.ai/keys.

Run:
    streamlit run streamlit_app.py
"""

import asyncio
import os

import streamlit as st
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

load_dotenv()

# Free tier slugs on OpenRouter rotate often — if this one 404s or
# rate-limits, check openrouter.ai/models filtered to price = $0 and
# "tools" support, and swap it here.
MODEL_NAME = "openrouter/free"

st.set_page_config(page_title="Library Assistant", page_icon="📚", layout="centered")


def build_openrouter_model() -> OpenAIChatCompletionsModel:
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        st.error(
            "API_TOKEN is not set. Add it to a .env file (get a free key "
            "at https://openrouter.ai/keys) and restart the app."
        )
        st.stop()
    client = AsyncOpenAI(api_key=api_token, base_url="https://openrouter.ai/api/v1")
    return OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)


async def run_turn(history, user_message):
    """Runs one conversational turn against a fresh MCP server connection."""
    set_tracing_disabled(True)
    model = build_openrouter_model()

    async with MCPServerStdio(
        name="Library Server",
        params={"command": "python", "args": ["app.py"]},
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

        new_input = history + [{"role": "user", "content": user_message}]
        result = await Runner.run(agent, new_input)

        tool_calls = []
        for item in result.new_items:
            if item.type == "tool_call_item":
                tool_calls.append({"name": item.tool_name, "output": None})
            elif item.type == "tool_call_output_item" and tool_calls:
                if tool_calls[-1]["output"] is None:
                    tool_calls[-1]["output"] = item.output

        return result.to_input_list(), result.final_output, tool_calls


def render_tool_calls(tool_calls):
    with st.expander(f"🔧 {len(tool_calls)} tool call(s)"):
        for i, tc in enumerate(tool_calls, 1):
            st.markdown(f"**[{i}] `{tc['name']}`**")
            out = tc["output"]
            text = out.get("text") if isinstance(out, dict) else out
            st.code(text or "", language=None)


# ---------- Session state ----------
if "history" not in st.session_state:
    st.session_state.history = []  # agent-SDK input list — carries context between turns
if "display" not in st.session_state:
    st.session_state.display = []  # [{role, content, tool_calls?}] — what's rendered

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 📚 Library Assistant")
    st.caption(f"Model: `{MODEL_NAME}`")
    st.caption("Connects to your local MCP library server (app.py) over stdio.")
    if st.button("Reset conversation"):
        st.session_state.history = []
        st.session_state.display = []
        st.rerun()

st.title("📚 Library Assistant")
st.caption("Search the catalog, check availability, or borrow/return books for a member.")

# ---------- Render prior turns ----------
for msg in st.session_state.display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            render_tool_calls(msg["tool_calls"])

# ---------- New input ----------
user_message = st.chat_input(
    "e.g. Find me books about space, then borrow one for member M001."
)

if user_message:
    st.session_state.display.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Working..."):
            try:
                new_history, final_output, tool_calls = asyncio.run(
                    run_turn(st.session_state.history, user_message)
                )
                st.session_state.history = new_history
                st.markdown(final_output)
                if tool_calls:
                    render_tool_calls(tool_calls)
                st.session_state.display.append(
                    {"role": "assistant", "content": final_output, "tool_calls": tool_calls}
                )
            except Exception as e:
                error_text = f"Something went wrong: {e}"
                st.error(error_text)
                st.session_state.display.append({"role": "assistant", "content": error_text})
