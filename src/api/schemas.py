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


class ConversationResponse(BaseModel):
    thread_id: str
    messages: list[Message]
