from pydantic import BaseModel


class ChatRequest(BaseModel):
    thread_id: str
    message: str


class Message(BaseModel):
    role: str  # "user" | "assistant" | "tool"
    content: str


class ThreadList(BaseModel):
    threads: list[str]


class ToolList(BaseModel):
    tools: list[str]
    # False while the MCP server's tools haven't loaded yet (e.g. it's still
    # cold-starting) — lets the UI keep polling instead of caching a partial list.
    mcp_ready: bool


class ConversationResponse(BaseModel):
    thread_id: str
    messages: list[Message]


class PdfIngestResponse(BaseModel):
    source: str
    pages: int
    chunks: int
    characters: int
