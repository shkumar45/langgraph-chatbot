# backend.py

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from ddgs import DDGS
from dotenv import load_dotenv
import sqlite3
import requests

load_dotenv()

# -------------------
# 1. LLM
# -------------------
llm = ChatOpenAI()

# -------------------
# 2. Tools
# -------------------
# Tools
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
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()



tools = [web_search, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools)

# -------------------
# 3. State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------------------
# 4. Nodes
# -------------------
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# -------------------
# 5. Checkpointer
# -------------------
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# -------------------
# 6. Graph
# -------------------
graph = (
    StateGraph(ChatState)
    .add_node('chat_node', chat_node)
    .add_node("tools", tool_node)
    .add_edge(START, 'chat_node')
    .add_conditional_edges("chat_node",tools_condition)
    .add_edge('tools', 'chat_node')
)

chatbot = graph.compile(checkpointer=checkpointer)

# -------------------
# 7. Helper
# -------------------
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)

if __name__ == "__main__":
    initial_state = {
        'messages': [HumanMessage(content='Write a 500 word paragraph on soccer world cup')]
    }
    print(chatbot.invoke(initial_state)['messages'][-1].content)
    for message_chunk, metadata in chatbot.stream(
        initial_state, 
        config = {'configurable': {'thread_id': 'thread-1'}}, 
        stream_mode='messages'
        ):
        if message_chunk.content:
            print(message_chunk.content, end= " ", flush=True)
        