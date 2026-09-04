"""Remote tools served over MCP.

`load_mcp_tools()` fetches the current tool list from every configured MCP
server. It's async because the adapter opens a connection to each server, and
it's time-boxed: a slow or cold-starting MCP server must never block app
startup (FastAPI's lifespan) or a chat turn — it just means fewer tools.
"""
import asyncio
import logging

from langchain_mcp_adapters.client import MultiServerMCPClient

import config

logger = logging.getLogger(__name__)

MCP_SERVERS = {
    "calculator": {
        "transport": "streamable_http",  # if this fails, try "sse"
        "url": config.MCP_CALCULATOR_URL,
    },
}

client = MultiServerMCPClient(MCP_SERVERS)


async def load_mcp_tools() -> list:
    """Return the tools currently exposed by the configured MCP servers.

    Returns [] (instead of raising) on timeout or connection failure, so a
    down/cold MCP server degrades the agent to its local tools rather than
    blocking startup or a turn.
    """
    if not MCP_SERVERS:
        return []
    try:
        return await asyncio.wait_for(
            client.get_tools(), timeout=config.MCP_TOOLS_TIMEOUT
        )
    except (TimeoutError, asyncio.TimeoutError):
        logger.warning(
            "MCP tool discovery timed out after %ss; continuing with local "
            "tools only.",
            config.MCP_TOOLS_TIMEOUT,
        )
        return []
    except Exception:
        logger.warning("MCP tool discovery failed; continuing with local tools only.", exc_info=True)
        return []
