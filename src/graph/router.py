"""Conditional-edge routing for the agent graph."""
from langgraph.graph import END

from state import ChatState


def route_after_chat(state: ChatState) -> str:
    """Route out of `chat_node`.

    -> "tools"  when the model's last message requested a tool call
    -> END      otherwise (the turn is finished)
    """
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END
