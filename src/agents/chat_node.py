"""The agent's reasoning node.

`make_chat_node` owns the model: it binds the given tools to the LLM and puts a
ChatPromptTemplate in front so a system prompt is injected on every turn without
being persisted to graph state.
"""
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

import config
from state import ChatState

llm = ChatOpenAI(model=config.OPENAI_MODEL)

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools: web search, stock "
    "prices, a calculator, and a PDF knowledge base.\n"
    "- Use `web_search` for current events or facts you are unsure of.\n"
    "- When the user gives a PDF path or URL, call `ingest_pdf`, then use "
    "`search_pdf` to answer questions about it and cite page numbers.\n"
    "- Prefer calling a tool over guessing. If a tool returns an error, say so "
    "plainly instead of inventing an answer.\n"
    "- Keep answers concise."
)

# A literal SystemMessage is passed through as-is (not treated as a template),
# so the prompt text can contain any characters safely.
_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


def make_chat_node(tools):
    """Return the `chat_node` coroutine, with `tools` bound to the model."""
    llm_with_tools = llm.bind_tools(tools) if tools else llm
    chain = _PROMPT | llm_with_tools

    async def chat_node(state: ChatState):
        """LLM node that either answers or requests a tool call."""
        response = await chain.ainvoke({"messages": state["messages"]})
        return {"messages": [response]}

    return chat_node
