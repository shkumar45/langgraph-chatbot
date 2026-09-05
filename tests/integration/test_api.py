"""API-level integration tests via FastAPI's TestClient (real graph, real
OpenAI calls) — run with `pytest -m integration`."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_health_and_tools_endpoints(require_real_openai_key):
    from api.app import app

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        tools = client.get("/tools").json()["tools"]
        assert "web_search" in tools


def test_chat_stream_end_to_end(require_real_openai_key):
    from api.app import app

    with TestClient(app) as client:
        body = {"thread_id": "it-api-1", "message": "Reply with exactly one word: banana."}
        with client.stream("POST", "/chat/stream", json=body) as response:
            assert response.status_code == 200
            text = "".join(response.iter_text())
        assert "banana" in text.lower()

        threads = client.get("/threads").json()["threads"]
        assert "it-api-1" in threads

        messages = client.get("/threads/it-api-1/messages").json()["messages"]
        roles = [m["role"] for m in messages]
        assert "user" in roles and "assistant" in roles
