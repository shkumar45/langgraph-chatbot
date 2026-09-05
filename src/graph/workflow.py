import aiosqlite
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode

import config
from agents import make_chat_node
from state import ChatState
from tools import LOCAL_TOOLS, get_all_tools

from .router import route_after_chat

_checkpointer = None  # BaseCheckpointSaver, built once per process
_tool_names: list[str] = []  # names resolved the last time build_graph() ran


async def get_checkpointer():
    """Process-wide checkpointer, chosen by ``config.CHECKPOINTER``:

    - ``"sqlite"`` -> ``AsyncSqliteSaver`` over ``config.CHECKPOINT_DB``
    - ``"memory"`` -> ``InMemorySaver`` (history lost when the process exits)
    """
    global _checkpointer
    if _checkpointer is None:
        if config.CHECKPOINTER == "sqlite":
            conn = await aiosqlite.connect(config.CHECKPOINT_DB)
            _checkpointer = AsyncSqliteSaver(conn)
        else:
            _checkpointer = InMemorySaver()
        print(f"Checkpointer: {type(_checkpointer).__name__}")
    return _checkpointer


def get_tool_names() -> list[str]:
    """Names of the tools resolved the last time build_graph() ran."""
    return list(_tool_names)


def mcp_tools_missing() -> bool:
    """True if the last build_graph() run didn't pick up any MCP tools

    (i.e. every resolved tool is one of the local ones) — signals it's worth
    retrying once the MCP server may have woken up.
    """
    return len(_tool_names) <= len(LOCAL_TOOLS)


async def build_graph():
    """Wire the StateGraph (nodes + edges) and compile it with the configured
    checkpointer. Tools (local + MCP) are resolved here and shared by the chat
    node and the tool node."""
    global _tool_names
    tools = await get_all_tools()
    _tool_names = [t.name for t in tools]

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", make_chat_node(tools))
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", route_after_chat)
    graph.add_edge("tools", "chat_node")

    return graph.compile(checkpointer=await get_checkpointer())
