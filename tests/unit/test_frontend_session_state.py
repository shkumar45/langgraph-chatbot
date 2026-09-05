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


def test_init_retries_tool_names_until_the_list_is_non_empty(fake_state, monkeypatch):
    """Regression test: an empty result from a cold API must not be cached
    forever — see the tool_names caching bug fixed in session_state.init()."""
    calls = {"n": 0}

    def fake_list_tools():
        calls["n"] += 1
        return [] if calls["n"] < 3 else ["web_search", "calculator"]

    monkeypatch.setattr(mod.api_client, "list_tools", fake_list_tools)
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])

    mod.init()
    assert fake_state["tool_names"] == []

    mod.init()
    assert fake_state["tool_names"] == []

    mod.init()
    assert fake_state["tool_names"] == ["web_search", "calculator"]

    mod.init()  # already non-empty -> must not call the API again
    assert calls["n"] == 3


def test_init_seeds_api_base_url_and_pushes_it_into_api_client(fake_state, monkeypatch):
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: ["x"])
    monkeypatch.setattr(mod.settings, "API_BASE_URL", "https://seeded.example.com")

    pushed = {}
    monkeypatch.setattr(mod.api_client, "set_base_url", lambda url: pushed.setdefault("url", url))

    mod.init()

    assert fake_state["api_base_url"] == "https://seeded.example.com"
    assert pushed["url"] == "https://seeded.example.com"


def test_init_fetches_threads_only_once(fake_state, monkeypatch):
    calls = {"n": 0}

    def fake_list_threads():
        calls["n"] += 1
        return ["t1"]

    monkeypatch.setattr(mod.api_client, "list_threads", fake_list_threads)
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: ["x"])

    mod.init()
    mod.init()

    assert calls["n"] == 1
    # init() also appends the (freshly generated) current thread_id.
    assert fake_state["chat_threads"] == ["t1", fake_state["thread_id"]]


def test_reset_chat_starts_a_new_thread_and_clears_history(fake_state, monkeypatch):
    monkeypatch.setattr(mod.api_client, "list_threads", lambda: [])
    monkeypatch.setattr(mod.api_client, "list_tools", lambda: [])
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
