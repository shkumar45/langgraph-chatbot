from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()  # Load environment variables from .env file

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm = ChatOpenAI()

def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # send to llm
    response = llm.invoke(messages)

    # response store state
    return {'messages': [response]}

conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = (
    StateGraph(ChatState)
    .add_node('chat_node', chat_node)
    .add_edge(START, 'chat_node')
    .add_edge('chat_node', END)
)



chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads(): 
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)

# initial_state = {
#     'messages': [HumanMessage(content='Write a 500 word paragraph on soccer world cup')]
# }

# print(chatbot.invoke(initial_state)['messages'][-1].content)

# for message_chunk, metadata in chatbot.stream(
#     initial_state, 
#     config = {'configurable': {'thread_id': 'thread-1'}}, 
#     stream_mode='messages'
#     ):
#     if message_chunk.content:
#         print(message_chunk.content, end= " ", flush=True)
        