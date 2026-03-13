from langgraph.graph import StateGraph, START, END
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import TypedDict
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

#for tools
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
import requests
import random

#put your api key here for huggingface
os.environ["HUGGINGFACE_ACCESS_TOKEN"] = "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"


load_dotenv()

# Tools
search_tool = DuckDuckGoSearchRun()

@tool
def calculator(first_num: float, second_num: float, operation: str) -> str:
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
                return "Division by zero is not allowed."
            result = first_num / second_num
        else:
            return f"Unsupported operation '{operation}'."
        
        return f"The result of {first_num} {operation} {second_num} is {result}."
    except Exception as e:
        return f"Error in calculation: {str(e)}"



@tool
def get_stock_price(symbol: str) -> str:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=GZN7KUKWRHBV3V8I"
    r = requests.get(url)
    return r.json()

#add tools to a tool node
tools = [search_tool, get_stock_price, calculator]
tool_node=ToolNode(tools=tools)

# Define state for LLM with messages for streaming support
class LLMState(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize LLM
llm = HuggingFaceEndpoint(
    model="Qwen/Qwen2.5-7B-Instruct",
    task="text-generation",
    huggingfacehub_api_token=os.environ["HUGGINGFACE_ACCESS_TOKEN"]
)

model = ChatHuggingFace(llm=llm, tools=tools)

# Define function for LLM to answer question
def chat_node(state: LLMState) -> LLMState:
    messages = state['messages']
    # Add system message to encourage tool use
    system_message = SystemMessage(content="You are a helpful assistant with access to tools. Always use the available tools to answer questions - do not perform calculations yourself or provide information from your training data. For ANY calculations, use the calculator tool. For stock prices, use the get_stock_price tool. For web searches, use the search tool. Always start your response by clearly stating which tool you will use, then provide the answer based ONLY on tool results. NEVER give answers without using the appropriate tool.")
    full_messages = [system_message] + messages
    response = model.invoke(full_messages)
    return {'messages': [response]}

# Initialize graph
graph = StateGraph(LLMState)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools', 'chat_node')
graph.add_edge("chat_node", END)

config = {'configurable': {'thread_id': '1'}}

conn=sqlite3.connect('chatbot_conversations.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

chatbot_workflow = graph.compile(checkpointer=checkpointer)



def retrieve_all_threads(): 
    all_threads=set()
    for checkpoint in checkpointer.list(None):
        configurable = checkpoint.config.get('configurable', {})
        if 'thread_id' in configurable:
            all_threads.add(configurable['thread_id'])

    return list(all_threads)





