from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

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

graph = (
    StateGraph(ChatState)
    .add_node('chat_node', chat_node)
    .add_edge(START, 'chat_node')
    .add_edge('chat_node', END)
)


checkpointer = InMemorySaver()
chatbot = graph.compile(checkpointer=checkpointer)

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
        