"""Centralised configuration.

Importing this module loads the project's .env file exactly once and exposes
the environment values the app needs as plain module-level constants.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# .env lives at the repo root (one level up from src/); fall back to the
# default upward search if it isn't there (e.g. on a deployed host).
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH if _ENV_PATH.exists() else None)

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# --- Tools ---
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
MCP_CALCULATOR_URL = os.getenv(
    "MCP_CALCULATOR_URL",
    "https://calculator-mcp-server-7prd.onrender.com/mcp",
)

# --- Persistence ---
CHECKPOINT_DB = os.getenv("CHECKPOINT_DB", "chatbot.db")

# --- API server ---
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", os.getenv("PORT", "8000")))

# --- LangSmith / tracing (read directly by the langchain SDK; exposed here
# for visibility) ---
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
