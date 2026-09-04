"""Remote tools served over MCP.

`load_mcp_tools()` fetches the current tool list from every configured MCP
server. It's async because the adapter opens a connection to each server.
"""
from langchain_mcp_adapters.client import MultiServerMCPClient

import config

MCP_SERVERS = {
    "calculator": {
        "transport": "streamable_http",  # if this fails, try "sse"
        "url": config.MCP_CALCULATOR_URL,
    },
}

client = MultiServerMCPClient(MCP_SERVERS)


async def load_mcp_tools() -> list:
    """Return the tools currently exposed by the configured MCP servers."""
    if not MCP_SERVERS:
        return []
    return await client.get_tools()
