"""FastAPI layer: HTTP routing + streaming for the LangGraph agent."""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

import config  # noqa: F401  -- imported for side effect: loads .env
from graph import build_graph, get_checkpointer

from . import service
from .schemas import ChatRequest, ConversationResponse, ThreadList


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the graph on FastAPI's own event loop so the checkpointer's
    # aiosqlite connection is bound to the loop that will use it.
    app.state.checkpointer = await get_checkpointer()
    app.state.chatbot = await build_graph()
    yield


app = FastAPI(title="LangGraph Chatbot API", lifespan=lifespan)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/threads", response_model=ThreadList)
async def threads():
    return ThreadList(threads=await service.list_threads(app.state.checkpointer))


@app.get("/threads/{thread_id}/messages", response_model=ConversationResponse)
async def conversation(thread_id: str):
    messages = await service.get_messages(app.state.chatbot, thread_id)
    return ConversationResponse(thread_id=thread_id, messages=messages)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream one assistant turn as Server-Sent Events.

    Events: `token` {content}, `tool` {name}, `error` {message}, `done` {}.
    """
    async def event_source():
        try:
            async for evt in service.stream_turn(
                app.state.chatbot, req.thread_id, req.message
            ):
                yield _sse(evt["type"], evt)
        except Exception as e:  # surface failures to the client stream
            yield _sse("error", {"message": str(e)})
        finally:
            yield _sse("done", {})

    return StreamingResponse(event_source(), media_type="text/event-stream")
