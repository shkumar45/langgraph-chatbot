"""Streamlit UI pieces: sidebar, history, and the streamed assistant reply."""
import httpx
import streamlit as st

import api_client
import session_state


def render_sidebar() -> None:
    st.sidebar.title("LangGraph MCP Chatbot")
    st.sidebar.caption(f"API: {st.session_state['api_base_url']}")
    tool_names = st.session_state.get("tool_names") or []
    if tool_names:
        st.sidebar.caption(f"Tools Supported: {', '.join(tool_names)}")

    if st.sidebar.button("New Chat"):
        session_state.reset_chat()

    render_pdf_uploader()

    st.sidebar.title("My Conversations")
    for thread_id in st.session_state["chat_threads"]:
        if st.sidebar.button(str(thread_id), key=f"thread-{thread_id}"):
            session_state.switch_thread(thread_id)


def render_pdf_uploader() -> None:
    """Sidebar file uploader: sends a PDF to /pdf/ingest so `search_pdf` can
    use it. Ingests once per distinct file, not on every rerun."""
    st.sidebar.title("Knowledge Base")
    uploaded = st.sidebar.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded is None:
        return

    file_key = (uploaded.name, uploaded.size)
    if st.session_state.get("last_ingested_pdf") == file_key:
        st.sidebar.caption(f"✅ `{uploaded.name}` already ingested")
        return

    with st.sidebar.spinner(f"Ingesting `{uploaded.name}` …"):
        result = api_client.ingest_pdf(uploaded.getvalue(), uploaded.name)

    if "error" in result:
        st.sidebar.error(f"Ingest failed: {result['error']}")
        return

    st.session_state["last_ingested_pdf"] = file_key
    st.sidebar.success(
        f"Ingested `{result.get('source', uploaded.name)}` — "
        f"{result.get('pages')} pages, {result.get('chunks')} chunks."
    )


def render_history() -> None:
    for message in st.session_state["message_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def stream_assistant_reply(user_input: str) -> str:
    """Stream one assistant turn into the page and return the final text."""
    tool_status = {"box": None}

    def tokens():
        try:
            for event, data in api_client.stream_turn(
                st.session_state["thread_id"], user_input
            ):
                if event == "tool":
                    _show_tool_running(tool_status, data.get("name", "tool"))
                elif event == "token":
                    yield data.get("content", "")
                elif event == "error":
                    yield f"\n\n**Error:** {data.get('message', 'unknown error')}"
        except httpx.HTTPError as exc:
            yield f"\n\n**Could not reach the API at {api_client.get_base_url()}:** {exc}"

    reply = st.write_stream(tokens())

    if tool_status["box"] is not None:
        tool_status["box"].update(
            label="✅ Tool finished", state="complete", expanded=False
        )
    return reply


def _show_tool_running(tool_status: dict, name: str) -> None:
    label = f"🔧 Using `{name}` …"
    if tool_status["box"] is None:
        tool_status["box"] = st.status(label, expanded=True)
    else:
        tool_status["box"].update(label=label, state="running")
