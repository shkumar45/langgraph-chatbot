"""Tests for src/frontend/api_client.py — pure HTTP client, no Streamlit."""
import httpx
import pytest

import api_client
import settings


@pytest.fixture(autouse=True)
def restore_base_url():
    original = api_client.get_base_url()
    yield
    api_client.set_base_url(original)


def test_normalize_base_url_adds_https_and_trims_slash():
    assert settings.normalize_base_url("example.onrender.com/") == "https://example.onrender.com"
    assert settings.normalize_base_url("http://localhost:8000") == "http://localhost:8000"


def test_set_base_url_drives_requests(monkeypatch):
    api_client.set_base_url("my-api.onrender.com")
    assert api_client.get_base_url() == "https://my-api.onrender.com"

    captured = {}

    def fake_get(url, timeout=None):
        captured["url"] = url
        return _json_response({"tools": []})

    monkeypatch.setattr(httpx, "get", fake_get)
    api_client.list_tools()
    assert captured["url"] == "https://my-api.onrender.com/tools"


def _json_response(data):
    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return data

    return R()


class _StatusResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_is_healthy_true_on_200(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda url, timeout=None: _StatusResponse(200))
    assert api_client.is_healthy() is True


def test_is_healthy_false_on_error(monkeypatch):
    def boom(url, timeout=None):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "get", boom)
    assert api_client.is_healthy() is False


def test_wait_until_ready_returns_true_once_health_recovers(monkeypatch):
    calls = {"n": 0}

    def flaky_get(url, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("still cold")
        return _StatusResponse(200)

    monkeypatch.setattr(httpx, "get", flaky_get)
    monkeypatch.setattr(api_client.time, "sleep", lambda s: None)

    assert api_client.wait_until_ready(max_wait=60, interval=1) is True
    assert calls["n"] == 3


def test_wait_until_ready_gives_up_after_max_wait(monkeypatch):
    monkeypatch.setattr(
        httpx, "get", lambda url, timeout=None: (_ for _ in ()).throw(httpx.ConnectError("down"))
    )
    monkeypatch.setattr(api_client.time, "sleep", lambda s: None)

    assert api_client.wait_until_ready(max_wait=2, interval=1) is False


class FakeResponse:
    def __init__(self, json_data=None, status_code=200):
        self._json = json_data or {}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._json


def test_list_threads_happy_path(monkeypatch):
    monkeypatch.setattr(
        httpx, "get", lambda url, timeout=None: FakeResponse({"threads": ["a", "b"]})
    )
    assert api_client.list_threads() == ["a", "b"]


def test_list_threads_swallows_connection_errors(monkeypatch):
    def raise_error(url, timeout=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "get", raise_error)
    assert api_client.list_threads() == []


def test_list_tools_happy_path(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, timeout=None: FakeResponse({"tools": ["web_search", "add"], "mcp_ready": True}),
    )
    assert api_client.list_tools() == (["web_search", "add"], True)


def test_list_tools_treats_missing_mcp_ready_as_not_ready(monkeypatch):
    """An older API without the flag must not stop the UI from re-polling."""
    monkeypatch.setattr(
        httpx, "get", lambda url, timeout=None: FakeResponse({"tools": ["web_search"]})
    )
    assert api_client.list_tools() == (["web_search"], False)


def test_list_tools_swallows_connection_errors(monkeypatch):
    def raise_error(url, timeout=None):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "get", raise_error)
    assert api_client.list_tools() == ([], False)


def test_load_conversation_filters_out_tool_and_empty_rows(monkeypatch):
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "tool", "content": "[raw tool output]"},
        {"role": "assistant", "content": ""},
        {"role": "assistant", "content": "hello"},
    ]
    monkeypatch.setattr(
        httpx, "get", lambda url, timeout=None: FakeResponse({"messages": messages})
    )
    result = api_client.load_conversation("t1")
    assert result == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


class FakeStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        pass

    def iter_lines(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_stream_turn_parses_sse_events_and_stops_at_done(monkeypatch):
    lines = [
        "event: tool",
        'data: {"type": "tool", "name": "calculator"}',
        "",
        "event: token",
        'data: {"type": "token", "content": "42"}',
        "",
        "event: done",
        "data: {}",
        "",
        # anything after "done" must never be yielded
        "event: token",
        'data: {"type": "token", "content": "should not appear"}',
        "",
    ]
    monkeypatch.setattr(
        httpx, "stream", lambda method, url, json=None, timeout=None: FakeStreamResponse(lines)
    )

    events = list(api_client.stream_turn("t1", "what is 6*7"))

    assert events == [
        ("tool", {"type": "tool", "name": "calculator"}),
        ("token", {"type": "token", "content": "42"}),
    ]
