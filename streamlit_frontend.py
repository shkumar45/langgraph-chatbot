import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph_backend import chatbot
import uuid


# Utility functions
def generate_thread_id():
  
    return str(uuid.uuid4())


# session state to store chat messages
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

# Sidebar for configuration
st.sidebar.title("LangGraph Chatbot")
st.sidebar.button("New Chat")
st.sidebar.title("Old Conversations")
st.sidebar.text(st.session_state['thread_id'])


# load the chat messages from history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type Here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode = 'messages'
            )
        )
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    # ai_message = response['messages'][-1]

    # st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message.content})

    # with st.chat_message('assistant'):
    #     st.text(ai_message.content)
