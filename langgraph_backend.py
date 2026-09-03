# backend.py

import os
import re

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI, tools
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from ddgs import DDGS
from langchain_core.tools import tool, BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
import aiosqlite
import requests
import asyncio
import threading
import queue

load_dotenv()

# Dedicated async loop for backend tasks
_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()

def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


def run_async(coro):
    return _submit_async(coro).result()


def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)


llm = ChatOpenAI()

client = MultiServerMCPClient(
    {
        "calculator": {
            "transport": "streamable_http",  # if this fails, try "sse"
            "url": "https://calculator-mcp-server-7prd.onrender.com/mcp",
        }
        # "expense": {
        #     "transport": "streamable_http",  # if this fails, try "sse"
        #     "url": "https://splendid-gold-dingo.fastmcp.app/mcp"
        # }
    }
)

@tool
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web with DuckDuckGo and return a list of results.
    Each result is a dict with 'title', 'href' and 'body'.
    Use this for current events or facts the model may not know.
    """
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, region="us-en", max_results=max_results))
    except Exception as e:
        return [{"error": str(e)}]

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return {"error": "ALPHAVANTAGE_API_KEY is not set in the environment"}
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    r = requests.get(url)
    return r.json()


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


async def _init_checkpointer():
    conn = await aiosqlite.connect(database="chatbot.db")
    return AsyncSqliteSaver(conn)

checkpointer = run_async(_init_checkpointer())

async def build_graph():
    mcp_tools = await client.get_tools() if client else []
    tools = [web_search, get_stock_price, *mcp_tools]
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    print(f"Loaded tools: {[tool.name for tool in tools]}")

    async def chat_node(state: ChatState):
        """LLM node that may answer or request a tool call."""
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools) if tools else None

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, "chat_node")

    if tool_node:
        graph.add_node("tools", tool_node)
        graph.add_conditional_edges("chat_node", tools_condition)
        graph.add_edge("tools", "chat_node")
    else:
        graph.add_edge("chat_node", END)

    chatbot = graph.compile(checkpointer=checkpointer)
    # chatbot = graph.compile()
    return chatbot


# Module-level graph so importers (e.g. streamlit_frontend) can use it directly
chatbot = run_async(build_graph())


async def _alist_threads():
    all_threads = set()
    async for checkpoint in checkpointer.alist(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def retrieve_all_threads():
    return run_async(_alist_threads())


def get_conversation(thread_id):
    """Return the stored message history for a thread (sync wrapper)."""
    state = run_async(
        chatbot.aget_state({"configurable": {"thread_id": thread_id}})
    )
    return state.values.get("messages", []) if state else []


def stream_chat(messages, config):
    """
    Drive chatbot.astream(...) on the backend event loop and yield chunks
    synchronously, so Streamlit can consume it with st.write_stream.
    Yields (message_chunk, metadata) tuples (stream_mode="messages").
    """
    q: "queue.Queue" = queue.Queue()
    sentinel = object()

    async def _producer():
        try:
            async for chunk in chatbot.astream(
                {"messages": messages}, config=config, stream_mode="messages"
            ):
                q.put(chunk)
        except Exception as e:  # forward the error to the consumer
            q.put(e)
        finally:
            q.put(sentinel)

    submit_async_task(_producer())

    while True:
        item = q.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            raise item
        yield item

async def main():
    # chatbot = run_async(build_graph())
    chatbot = await build_graph()
    result = await chatbot.ainvoke(
        {"messages": [HumanMessage(content="Find the modulus of 132354 and 23 and give answer like a cricket commentator.")]},
        config={"configurable": {"thread_id": "main-thread"}},
    )
    print("Chatbot is ready.")
    print(result['messages'][-1].content)

if __name__ == "__main__":
    asyncio.run(main())