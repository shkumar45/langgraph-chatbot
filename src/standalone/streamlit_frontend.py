import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make src/ importable

import uuid  # noqa: E402

import streamlit as st  # noqa: E402
from langchain_core.messages import (  # noqa: E402
    AIMessage,
    HumanMessage,
    ToolMessage,
)

from standalone.langgraph_backend import (  # noqa: E402
    get_conversation,
    retrieve_all_threads,
    stream_chat,
)


# Utility functions
def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return get_conversation(thread_id)



# session state to store chat messages
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

# Sidebar for configuration
st.sidebar.title("LangGraph MCP Chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.title("My Conversations")
for thread_id in st.session_state['chat_threads']:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for message in messages:
            if isinstance(message, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role, 'content': message.content})

        st.session_state['message_history'] = temp_messages

# load the chat messages from history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type Here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    #CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    CONFIG = {
        'configurable': {'thread_id': st.session_state['thread_id']},
        'metadata': {
            "thread_id": st.session_state['thread_id']
        },
        'run_name': 'chat_turn'
    }

    with st.chat_message('assistant'):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}
        def ai_only_stream():
            for message_chunk, metadata in stream_chat(
                [HumanMessage(content=user_input)],
                CONFIG,
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    # ai_message = response['messages'][-1]

    # st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message.content})

    # with st.chat_message('assistant'):
    #     st.text(ai_message.content)
