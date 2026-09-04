"""Streamlit chat UI that talks to the FastAPI layer over HTTP.

It imports nothing from the agent — only `api_client` (HTTP). Run the API first:

    python src/main.py
    streamlit run src/frontend/streamlit_frontend.py
"""
import streamlit as st

import components
import session_state

session_state.init()

components.render_sidebar()
components.render_history()

user_input = st.chat_input("Type Here")
if user_input:
    session_state.append_message("user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        reply = components.stream_assistant_reply(user_input)

    session_state.append_message("assistant", reply)
