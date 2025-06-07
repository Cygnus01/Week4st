import streamlit as st
import os
import asyncio
from agents import Agent, Runner, WebSearchTool, FileSearchTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Ensure your OpenAI key is available from .env file
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
vector_store_id = os.environ["vector_store_id"]

# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize search tool preferences if they don't exist
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = True
if "use_file_search" not in st.session_state:
    st.session_state.use_file_search = True

# Function to create agent with selected tools
def create_research_assistant():
    tools = []
    
    if st.session_state.use_web_search:
        tools.append(WebSearchTool())
        
    if st.session_state.use_file_search:
        tools.append(FileSearchTool(
            max_num_results=3,
            vector_store_ids=[vector_store_id],
        ))
    
    return Agent(
        name="Toll Assistant",
        instructions="""You are a helpful Tolling Information Agent. Your main job is to provide clear, accurate, 
    and friendly information about toll charges, payment methods, and deadlines to avoid penalties. 
    Always remember to: - Clearly explain toll charges based on vehicle class (e.g., cars, vans, HGVs). - 
    Emphasize the deadline to pay before a Penalty Charge Notice (PCN) is issued. 
    Never: - Guess or give uncertain answers about payment or legal timeframes. 
    - Use jargon or overly technical language that could confuse the customer. When talking to users, be patient, clear, professional, and empathetic.
    Format your responses in a clear, readable manner using markdown formatting when appropriate.
        """,
        tools=tools,
    )

# Async wrapper for running the agent with memory
async def get_research_response(question, history):
    # Create agent with current tool selections
    research_assistant = create_research_assistant()
    
    # Combine history and current question to provide context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    prompt = f"Context of our conversation:\n{context}\n\nCurrent question: {question}"
    
    result = await Runner.run(research_assistant, prompt)
    return result.final_output

# Streamlit UI
st.set_page_config(page_title="Mersey Gateway Bridge Assistant", layout="wide")
st.title("🚗 Mersey Gateway Bridge Assistant")
st.write("Ask me anything, and I'll search for information to help answer your questions.")

# Sidebar controls for search tool selection
st.sidebar.title("Search Settings")

# Tool selection toggles
st.sidebar.subheader("Select Search Sources")
web_search = st.sidebar.checkbox("Web Search", value=st.session_state.use_web_search, key="web_search_toggle")
file_search = st.sidebar.checkbox("Vector Store Search", value=st.session_state.use_file_search, key="file_search_toggle")

# Update session state when toggles change
if web_search != st.session_state.use_web_search:
    st.session_state.use_web_search = web_search
    
if file_search != st.session_state.use_file_search:
    st.session_state.use_file_search = file_search

# Validate that at least one search source is selected
if not st.session_state.use_web_search and not st.session_state.use_file_search:
    st.sidebar.warning("Please select at least one search source")

# Conversation controls
st.sidebar.subheader("Conversation")
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.experimental_rerun()

# Display some helpful examples
with st.sidebar.expander("Example Questions"):
    st.markdown("""
    - What are the key findings in my vector store documents?
    - What is the latest news regarding the Mersey Gateway Bridge.
    - What are the latest statistics regarding the Mersey Gateway Bridge.
    - Summarize the information about "TOPIC" from my documents.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🚗 Made by the MerseyFlow BI Team")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_question = st.chat_input("Ask your Mersey Gateway Bridge question")

if user_question:
    # Check if at least one search source is selected
    if not st.session_state.use_web_search and not st.session_state.use_file_search:
        st.error("Please select at least one search source in the sidebar")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)
        
        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Researching..."):
                response_placeholder = st.empty()
                
                # Get response from agent
                response = asyncio.run(get_research_response(user_question, st.session_state.messages))
                
                # Update response placeholder
                response_placeholder.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
