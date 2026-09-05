"""Thin HTTP client for the chatbot API. No Streamlit here."""
import json

import httpx

import settings


def _get(path: str):
    response = httpx.get(
        f"{settings.API_BASE_URL}{path}", timeout=settings.REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def list_tools() -> list[str]:
    try:
        return _get("/tools")["tools"]
    except httpx.HTTPError:
        return []


def list_threads() -> list[str]:
    try:
        return _get("/threads")["threads"]
    except httpx.HTTPError:
        return []


def load_conversation(thread_id: str) -> list[dict]:
    """Displayable user/assistant turns for a thread (tool rows filtered out)."""
    try:
        messages = _get(f"/threads/{thread_id}/messages")["messages"]
    except httpx.HTTPError:
        return []
    return [
        m for m in messages
        if m["role"] in ("user", "assistant") and m["content"]
    ]


def stream_turn(thread_id: str, message: str):
    """Yield ``(event, data)`` from ``POST /chat/stream``.

    ``event`` is one of ``"token"``, ``"tool"``, ``"error"``; the terminating
    ``"done"`` event ends the generator. Raises ``httpx.HTTPError`` if the API
    can't be reached.
    """
    body = {"thread_id": thread_id, "message": message}
    with httpx.stream(
        "POST",
        f"{settings.API_BASE_URL}/chat/stream",
        json=body,
        timeout=settings.STREAM_TIMEOUT,
    ) as response:
        response.raise_for_status()
        event = None
        for line in response.iter_lines():
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                raw = line[len("data:"):].strip()
                try:
                    data = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    data = {"raw": raw}
                if event == "done":
                    return
                yield event, data
