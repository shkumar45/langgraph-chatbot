"""Standalone, run-directly entry points.

- `streamlit_frontend.py` — the in-process Streamlit chat UI
- `langgraph_backend.py`   — the async-loop + sync-bridge runtime it uses

Both add the `src/` directory to `sys.path` on startup so `graph`, `tools`,
`state`, `config` resolve when the file is launched directly.
"""
