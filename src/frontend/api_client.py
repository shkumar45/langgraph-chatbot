"""Thin HTTP client for the chatbot API. No Streamlit here."""
import json
import time

import httpx

import settings

# The base URL every request uses. Defaults to the env-derived value;
# session_state.init() calls set_base_url() so a per-session override takes
# effect for real requests, not just the sidebar display.
_base_url = settings.API_BASE_URL


def set_base_url(url: str) -> None:
    global _base_url
    _base_url = settings.normalize_base_url(url)


def get_base_url() -> str:
    return _base_url


def _get(path: str):
    response = httpx.get(f"{_base_url}{path}", timeout=settings.REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def is_healthy() -> bool:
    """One quick /health probe."""
    try:
        return (
            httpx.get(
                f"{_base_url}/health", timeout=settings.HEALTH_TIMEOUT
            ).status_code
            == 200
        )
    except httpx.HTTPError:
        return False


def wait_until_ready(
    max_wait: float | None = None, interval: float | None = None
) -> bool:
    """Poll /health until it answers 200 or `max_wait` seconds elapse.

    Covers the ~30-60s cold start when a Render free-tier service has spun
    down. Returns True as soon as the API responds, False on giving up.
    """
    max_wait = settings.API_WAKE_MAX_WAIT if max_wait is None else max_wait
    interval = settings.API_WAKE_INTERVAL if interval is None else interval
    deadline = time.monotonic() + max_wait
    while True:
        if is_healthy():
            return True
        if time.monotonic() + interval >= deadline:
            return False
        time.sleep(interval)


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


def ingest_pdf(file_bytes: bytes, filename: str) -> dict:
    """POST a PDF to /pdf/ingest. Returns the ingest summary or {"error": ...}."""
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        response = httpx.post(
            f"{_base_url}/pdf/ingest",
            files=files,
            timeout=settings.INGEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except (ValueError, AttributeError):
            detail = str(exc)
        return {"error": detail}
    except httpx.HTTPError as exc:
        return {"error": f"Could not reach the API: {exc}"}


def stream_turn(thread_id: str, message: str):
    """Yield ``(event, data)`` from ``POST /chat/stream``.

    ``event`` is one of ``"token"``, ``"tool"``, ``"error"``; the terminating
    ``"done"`` event ends the generator. Raises ``httpx.HTTPError`` if the API
    can't be reached.
    """
    body = {"thread_id": thread_id, "message": message}
    with httpx.stream(
        "POST",
        f"{_base_url}/chat/stream",
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
