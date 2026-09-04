"""Async glue between the HTTP layer and the compiled agent graph.

FastAPI runs on its own event loop, so everything here awaits the graph
directly — no sync bridge / background thread needed.
"""
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    ToolMessage,
)


async def stream_turn(chatbot, thread_id: str, message: str):
    """Yield {'type': 'token'|'tool', ...} events for one user turn."""
    run_config = {"configurable": {"thread_id": thread_id}}
    async for chunk, _meta in chatbot.astream(
        {"messages": [HumanMessage(content=message)]},
        config=run_config,
        stream_mode="messages",
    ):
        if isinstance(chunk, ToolMessage):
            yield {"type": "tool", "name": chunk.name or "tool"}
        elif isinstance(chunk, (AIMessage, AIMessageChunk)) and chunk.content:
            yield {"type": "token", "content": chunk.content}


async def list_threads(checkpointer) -> list[str]:
    seen: set[str] = set()
    async for checkpoint in checkpointer.alist(None):
        seen.add(checkpoint.config["configurable"]["thread_id"])
    return list(seen)


async def get_messages(chatbot, thread_id: str) -> list[dict]:
    state = await chatbot.aget_state({"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", []) if state else []

    out: list[dict] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            role = "user"
        elif isinstance(m, ToolMessage):
            role = "tool"
        else:
            role = "assistant"
        out.append({"role": role, "content": m.content if isinstance(m.content, str) else str(m.content)})
    return out
