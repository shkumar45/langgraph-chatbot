from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END

from graph.router import route_after_chat


def test_routes_to_tools_when_a_tool_call_is_present():
    state = {
        "messages": [
            HumanMessage(content="what's 6 * 7?"),
            AIMessage(
                content="",
                tool_calls=[{"name": "calculator", "args": {}, "id": "call_1"}],
            ),
        ]
    }
    assert route_after_chat(state) == "tools"


def test_routes_to_end_when_the_model_just_answers():
    state = {
        "messages": [
            HumanMessage(content="hi"),
            AIMessage(content="hello!"),
        ]
    }
    assert route_after_chat(state) == END
