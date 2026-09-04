import aiosqlite
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode

import config
from agents import make_chat_node
from state import ChatState
from tools import get_all_tools

from .router import route_after_chat

llm = ChatOpenAI(model=config.OPENAI_MODEL)

_checkpointer: AsyncSqliteSaver | None = None


async def get_checkpointer() -> AsyncSqliteSaver:
    """Process-wide AsyncSqliteSaver over the chat-history DB."""
    global _checkpointer
    if _checkpointer is None:
        conn = await aiosqlite.connect(config.CHECKPOINT_DB)
        _checkpointer = AsyncSqliteSaver(conn)
    return _checkpointer


async def build_graph():
    """Build the StateGraph, register nodes and edges, and compile it with the
    SQLite checkpointer. Tools (local + MCP) are resolved at call time."""
    tools = await get_all_tools()
    llm_with_tools = llm.bind_tools(tools) if tools else llm
    print(f"Loaded tools: {[t.name for t in tools]}")

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", make_chat_node(llm_with_tools))
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", route_after_chat)
    graph.add_edge("tools", "chat_node")

    return graph.compile(checkpointer=await get_checkpointer())
