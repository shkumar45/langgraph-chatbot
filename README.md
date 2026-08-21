# LangGraph Chatbot

A simple conversational chatbot built with [LangGraph](https://langchain-ai.github.io/langgraph/) and [Streamlit](https://streamlit.io/). It streams responses from an OpenAI model and persists chat history across sessions using a SQLite-backed checkpointer, so previous conversation threads can be reopened from the sidebar.

## How it works

- `langgraph_backend.py` defines a single-node LangGraph graph (`chat_node`) that sends the conversation state to `ChatOpenAI` and appends the response. State is persisted via `SqliteSaver`, with each conversation identified by a `thread_id` stored in `chatbot.db`.
- `streamlit_frontend.py` is the chat UI. It manages thread creation/switching, loads past conversations from the checkpointer, and streams assistant responses token-by-token.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```bash
   cp .env.sample .env
   ```
   Then edit `.env` and set your `OPENAI_API_KEY`.

## Running the app

```bash
streamlit run streamlit_frontend.py
```

This opens the chatbot in your browser. Use **New Chat** in the sidebar to start a fresh conversation thread, or select a past thread to resume it.

## Project structure

```
.
├── langgraph_backend.py    # LangGraph graph, LLM node, SQLite checkpointer
├── streamlit_frontend.py   # Streamlit chat UI
├── requirements.txt        # Python dependencies
├── .env.sample             # Template for required environment variables
└── chatbot.db               # SQLite database storing conversation threads (gitignored)
```
