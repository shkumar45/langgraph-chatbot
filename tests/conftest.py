"""Shared test setup.

Loads the real .env if present (so integration tests can use real keys), then
fills in safe dummies for anything still missing. Several modules construct an
OpenAI client at import time (agents/chat_node.py, tools/pdf.py) — that only
needs *a* key to be present to construct successfully, not a valid one, so
this keeps plain unit-test imports working with no credentials at all.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")

os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")
os.environ.setdefault("ALPHAVANTAGE_API_KEY", "test-dummy-key")
os.environ.setdefault("CHECKPOINTER", "memory")

import pytest  # noqa: E402


@pytest.fixture
def require_real_openai_key():
    """Skip a test unless a real OPENAI_API_KEY is configured."""
    import config

    if not config.OPENAI_API_KEY or "dummy" in config.OPENAI_API_KEY:
        pytest.skip("set a real OPENAI_API_KEY (e.g. in .env) to run this test")
