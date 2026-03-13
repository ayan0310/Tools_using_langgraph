# Tools_using_langgraph
🚀 Project Overview
This application demonstrates a sophisticated AI agent architecture using LangGraph to manage state and tool-calling logic. It uses the Qwen2.5-7B-Instruct model (via Hugging Face) to interact with users, and it is capable of autonomously deciding when to search the web, calculate math problems, or fetch real-time stock prices.

Key Features
Persistent Conversations: Uses SqliteSaver to store chat history, allowing users to resume threads later.

Streaming UI: A modern Streamlit interface that supports real-time message streaming.

Multi-Tool Integration: * Search: DuckDuckGo integration for real-time information.

Finance: Real-time stock quotes via Alpha Vantage API.

Math: A custom-built arithmetic calculator.

State Management: Utilizes LangGraph’s StateGraph to handle cycles between the LLM and tool execution.

🛠️ Architecture
The system is split into two main components:

1. Backend (langgraph_backend_with_tools.py)
This file defines the "brain" of the agent:

State Definition: Uses a TypedDict with add_messages to track the conversation flow.

Nodes: * chat_node: Handles the logic for the LLM to process messages and decide on tool usage.

tools: A ToolNode that executes the requested functions (Search, Calculator, Stock Price).

Edges: Defines the workflow starting from START, moving to the chat_node, and conditionally routing to tools or END based on the LLM's response.

2. Frontend (streamlit_frontend.py)
A user-friendly web interface:

Sidebar: Displays conversation history and a "New Chat" button to generate unique thread_ids.

Chat Interface: Handles user input and displays the assistant's streaming output.

Session State: Synchronizes the Streamlit UI with the SQLite backend to ensure continuity.

🔧 Installation & Setup
Prerequisites
Python 3.9+

Hugging Face Access Token

Alpha Vantage API Key (included in code)

Required Libraries
Bash
pip install langgraph langchain_huggingface streamlit langchain_community requests pysqlite3
Running the Application
Configure Environment: Ensure your .env file contains your Hugging Face token or use the one provided in the script.

Launch: Run the following command in your terminal:

Bash
streamlit run streamlit_frontend.py
📊 Graph Visualization
The workflow follows a cyclical pattern:

START → chat_node

chat_node → (Condition: Does the LLM want to use a tool?)

Yes → tools → back to chat_node

No → END

📝 Example Usage
Calculations: "What is 15% of 450?" (Invokes calculator).

Stocks: "What is the current price of AAPL?" (Invokes get_stock_price).

General Knowledge: "Who won the Super Bowl in 2026?" (Invokes search_tool).
