"""Agent tools — one module per tool.

- ``LOCAL_TOOLS``: the in-process tools (no I/O to construct).
- ``get_all_tools()``: ``LOCAL_TOOLS`` plus whatever the MCP servers expose.

Hand the result to ``llm.bind_tools`` / ``ToolNode``.
"""
import config  # noqa: F401  -- imported first for side effect: loads .env

from .calculator import calculator
from .mcp import client, load_mcp_tools
from .pdf import ingest_pdf, search_pdf
from .stock_price import get_stock_price
from .web_search import web_search

# `calculator` is intentionally left out — the MCP server already provides
# arithmetic tools; add it here to use the local one instead.
LOCAL_TOOLS = [web_search, get_stock_price, ingest_pdf, search_pdf]


async def get_all_tools() -> list:
    """Local tools plus the tools currently served by the MCP servers."""
    return [*LOCAL_TOOLS, *await load_mcp_tools()]


__all__ = [
    "calculator",
    "get_stock_price",
    "ingest_pdf",
    "search_pdf",
    "web_search",
    "LOCAL_TOOLS",
    "load_mcp_tools",
    "get_all_tools",
    "client",
]
