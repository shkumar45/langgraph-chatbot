"""Streamlit session-state setup and mutators."""
import uuid

import streamlit as st

import api_client
import settings


def generate_thread_id() -> str:
    return str(uuid.uuid4())


def init() -> None:
    """Populate session state on first run of a session."""
    st.session_state.setdefault("message_history", [])
    st.session_state.setdefault("thread_id", generate_thread_id())
    # Base URL of the API. Seeded from the environment; kept in session state
    # so it can be overridden per session, and pushed into api_client so the
    # override actually drives requests.
    st.session_state.setdefault("api_base_url", settings.API_BASE_URL)
    api_client.set_base_url(st.session_state["api_base_url"])
    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = api_client.list_threads()
    # Retry (not just once) until we get a non-empty list: right after a cold
    # start the API may briefly report zero/local-only tools while its own
    # MCP retry is still in flight.
    if not st.session_state.get("tool_names"):
        st.session_state["tool_names"] = api_client.list_tools()
    add_thread(st.session_state["thread_id"])


def add_thread(thread_id: str) -> None:
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat() -> None:
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []


def switch_thread(thread_id: str) -> None:
    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = [
        {"role": m["role"], "content": m["content"]}
        for m in api_client.load_conversation(thread_id)
    ]


def append_message(role: str, content: str) -> None:
    st.session_state["message_history"].append({"role": role, "content": content})
