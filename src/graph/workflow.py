import aiosqlite
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode

import config
from agents import make_chat_node
from state import ChatState
from tools import get_all_tools

from .router import route_after_chat

_checkpointer = None  # BaseCheckpointSaver, built once per process


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


async def build_graph():
    """Wire the StateGraph (nodes + edges) and compile it with the configured
    checkpointer. Tools (local + MCP) are resolved here and shared by the chat
    node and the tool node."""
    tools = await get_all_tools()

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", make_chat_node(tools))
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", route_after_chat)
    graph.add_edge("tools", "chat_node")

    return graph.compile(checkpointer=await get_checkpointer())
