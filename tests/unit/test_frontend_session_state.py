"""Tests for src/frontend/session_state.py.

A plain dict stands in for st.session_state — it supports the same
.setdefault()/.get()/[]/`in` operations session_state.py relies on.
"""
import pytest

import session_state as mod


@pytest.fixture
def fake_state(monkeypatch):
    state: dict = {}
    monkeypatch.setattr(mod.st, "session_state", state)
    return state


def test_init_refetches_tools_until_mcp_is_ready(fake_state, monkeypatch):
    """Regression test: neither an empty result from a cold API nor a
    local-only list (MCP server still cold) may be cached for the session."""
    responses = [
        ([], False),                                  # API unreachable
        (["web_search"], False),                      # API up, MCP still cold
        (["web_search", "add"], True),                # MCP tools loaded
    ]
    calls = {"n": 0}

    def fake_list_tools():
        calls["n"] += 1
        return responses[min(calls["n"], len(responses)) - 1]

    monkeypatch.setattr(mod.api_client, "list_tools", fake_list_tools)
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])

    mod.init()
    assert fake_state["tool_names"] == []
    assert fake_state["mcp_ready"] is False

    mod.init()
    assert fake_state["tool_names"] == ["web_search"]
    assert fake_state["mcp_ready"] is False

    mod.init()
    assert fake_state["tool_names"] == ["web_search", "add"]
    assert fake_state["mcp_ready"] is True

    mod.init()  # MCP ready -> must not call the API again
    assert calls["n"] == 3


def test_init_keeps_last_tool_list_if_api_drops_out(fake_state, monkeypatch):
    responses = iter([(["web_search"], False), ([], False)])
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: next(responses))
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])

    mod.init()
    mod.init()

    assert fake_state["tool_names"] == ["web_search"]


def test_init_seeds_api_base_url_and_pushes_it_into_api_client(fake_state, monkeypatch):
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: (["x"], True))
    monkeypatch.setattr(mod.settings, "API_BASE_URL", "https://seeded.example.com")

    pushed = {}
    monkeypatch.setattr(mod.api_client, "set_base_url", lambda url: pushed.setdefault("url", url))

    mod.init()

    assert fake_state["api_base_url"] == "https://seeded.example.com"
    assert pushed["url"] == "https://seeded.example.com"


def test_init_seeds_api_ready_false(fake_state, monkeypatch):
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: (["x"], True))
    mod.init()
    assert fake_state["api_ready"] is False


def test_init_fetches_threads_only_once(fake_state, monkeypatch):
    calls = {"n": 0}

    def fake_list_threads():
        calls["n"] += 1
        return ["t1"]

    monkeypatch.setattr(mod.api_client, "list_threads", fake_list_threads)
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: (["x"], True))

    mod.init()
    mod.init()

    assert calls["n"] == 1
    # init() also appends the (freshly generated) current thread_id.
    assert fake_state["chat_threads"] == ["t1", fake_state["thread_id"]]


def test_reset_chat_starts_a_new_thread_and_clears_history(fake_state, monkeypatch):
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: ([], False))
    mod.init()
    old_thread = fake_state["thread_id"]
    fake_state["message_history"] = [{"role": "user", "content": "hi"}]

    mod.reset_chat()

    assert fake_state["thread_id"] != old_thread
    assert fake_state["message_history"] == []
    assert fake_state["thread_id"] in fake_state["chat_threads"]


def test_switch_thread_loads_history_from_the_api(fake_state, monkeypatch):
    monkeypatch.setattr(
        mod.api_client,
        "load_conversation",
        lambda thread_id: [{"role": "user", "content": f"hello from {thread_id}"}],
    )

    mod.switch_thread("t2")

    assert fake_state["thread_id"] == "t2"
    assert fake_state["message_history"] == [
        {"role": "user", "content": "hello from t2"}
    ]
