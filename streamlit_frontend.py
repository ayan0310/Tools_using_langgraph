import streamlit as st
from langgraph_backend_with_tools import chatbot_workflow,retrieve_all_threads
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
import uuid

#....................................Thread Management/Utility Functions................................#

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    st.session_state["thread_id"] = generate_thread_id()
    add_thread(st.session_state["thread_id"])
    st.session_state["message_history"] = []

def add_thread(thread_id, title="New Chat"):
    if thread_id not in [t["id"] for t in st.session_state["chat_threads"]]:
        st.session_state["chat_threads"].append({"id": thread_id, "title": title})

def update_thread_title(thread_id, title):
    for thread in st.session_state["chat_threads"]:
        if thread["id"] == thread_id:
            thread["title"] = title[:50] + "..." if len(title) > 50 else title
            break

def load_conversation(thread_id):
    state = chatbot_workflow.get_state({'configurable': {'thread_id': thread_id}})
    if state.values and 'messages' in state.values:
        return state.values['messages']
    return []

#..............................................Session Setup..........................................#

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    # Convert thread IDs from database to expected format with id and title
    thread_ids = retrieve_all_threads()
    st.session_state["chat_threads"] = []
    for tid in thread_ids:
        # Load first message as title, or use thread ID if no messages
        messages = load_conversation(tid)
        if messages and len(messages) > 0:
            first_msg = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
            title = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
        else:
            title = "New Chat"
        st.session_state["chat_threads"].append({"id": tid, "title": title})

add_thread(st.session_state["thread_id"])

#................................................Sidebar UI ..........................................#

 # Define your title and the gradient colors
title_text = "LangGraph Chatbot with Streamlit (Streaming Version)"

# Use HTML and inline CSS to create the gradient effect
gradient_html = f"""
    <h1 style="
        background: linear-gradient(to right, #ff00cc, #333399); 
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: sans-serif;
        font-weight: bold;
        margin-top: -20px;
    ">
        {title_text}
    </h1>
"""

# Render the HTML in the sidebar
st.sidebar.markdown(gradient_html, unsafe_allow_html=True)

# Add custom CSS for fixed-size sidebar buttons
st.markdown("""
<style>
    /* Chat message styling - no blocks */
    [data-testid="stChatMessage"] {
        background: transparent;
        border: none;
    }
    
    [data-testid="stSidebar"] .stButton {
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        min-width: 250px;
        max-width: 250px;
        height: 45px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: left;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        box-sizing: border-box;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread in st.session_state["chat_threads"][::-1]:  # Show most recent threads at the top
    # Only show threads that have actual messages (not "New Chat")
    if thread["title"] == "New Chat":
        continue
    if st.sidebar.button(thread["title"], key=thread["id"]):
        st.session_state["thread_id"] = thread["id"]
        messages=load_conversation(thread["id"])

        temp_messages=[]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            elif isinstance(msg, ToolMessage):
                role='assistant'  # Show tool results as assistant messages
            else:
                role='assistant'
            temp_messages.append({"role": role, "content": msg.content})
        st.session_state["message_history"] = temp_messages


#print the message history
for message in st.session_state["message_history"]:
      with st.chat_message(message["role"]):
            st.markdown(message["content"])

#get user input and add it into the message history, then invoke the workflow to get chatbot output and add it into the message history
user_input = st.chat_input("Ask a question: ")
if user_input:
    # Update thread title with first message if this is the first message
    if len(st.session_state["message_history"]) == 0:
        update_thread_title(st.session_state["thread_id"], user_input)
    
    #add the user input into the message history
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    #show chatbot output in streaming way and add it into the message history
    with st.chat_message("assistant"):
        config: RunnableConfig = {'configurable': {'thread_id': st.session_state["thread_id"]}}
        
        full_response = ""
        message_placeholder = st.empty()
        for message_chunk, metadata in chatbot_workflow.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=config,
            stream_mode='messages'
        ):
            # Check if the chunk is an AIMessageChunk and has content
            if isinstance(message_chunk, AIMessageChunk) and isinstance(message_chunk.content, str):
                full_response += message_chunk.content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
    st.session_state["message_history"].append({"role": "assistant", "content": full_response})
        