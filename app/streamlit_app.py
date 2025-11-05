import streamlit as st
import requests
import json
from typing import List, Dict
import os

# Page configuration
st.set_page_config(
    page_title="Banking Chatbot",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rasa_url" not in st.session_state:
    st.session_state.rasa_url = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
if "api_status" not in st.session_state:
    st.session_state.api_status = "unknown"

# Header
st.markdown('<p class="main-header">🏦 Banking GenAI Assistant</p>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Rasa URL configuration
    rasa_url = st.text_input(
        "Rasa Webhook URL",
        value=st.session_state.rasa_url,
        help="URL of the Rasa REST webhook endpoint"
    )
    st.session_state.rasa_url = rasa_url
    
    # API Status check
    st.subheader("🔌 Connection Status")
    
    if st.button("Check Rasa Connection"):
        try:
            # Try to connect to Rasa health endpoint
            health_url = rasa_url.replace("/webhooks/rest/webhook", "/")
            response = requests.get(health_url, timeout=2)
            if response.status_code < 500:
                st.session_state.api_status = "connected"
                st.success("✅ Rasa server is connected!")
            else:
                st.session_state.api_status = "error"
                st.error("❌ Rasa server returned an error")
        except requests.exceptions.ConnectionError:
            st.session_state.api_status = "disconnected"
            st.error("❌ Cannot connect to Rasa server. Make sure it's running on port 5005.")
        except Exception as e:
            st.session_state.api_status = "error"
            st.error(f"❌ Error: {str(e)}")
    
    # Display status
    if st.session_state.api_status == "connected":
        st.success("Status: Connected")
    elif st.session_state.api_status == "disconnected":
        st.error("Status: Disconnected")
    else:
        st.info("Status: Unknown - Click 'Check Rasa Connection'")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    # Example queries
    st.subheader("💡 Example Queries")
    example_queries = [
        "What is my checking account balance?",
        "Show me my recent transactions",
        "Analyze my spending patterns",
        "Transfer 500 dollars from checking to savings",
        "What is overdraft protection?",
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{hash(query)}", use_container_width=True):
            st.session_state.user_input = query
            st.rerun()

# Main chat interface
st.subheader("💬 Chat with your Banking Assistant")

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

# Handle user input
if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_input)
    
    # Get response from Rasa
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Send request to Rasa
                response = requests.post(
                    st.session_state.rasa_url,
                    json={"sender": "user", "message": user_input},
                    timeout=10
                )
                response.raise_for_status()
                
                # Parse Rasa response
                rasa_response = response.json()
                
                # Extract bot messages
                if isinstance(rasa_response, list):
                    bot_messages = [msg.get("text", "") for msg in rasa_response if msg.get("text")]
                    if bot_messages:
                        bot_response = "\n".join(bot_messages)
                    else:
                        # If empty, check if action was triggered but didn't respond
                        bot_response = "I received your message but didn't get a response. This might mean:\n" \
                                     "1. The action server isn't running or reachable\n" \
                                     "2. The action encountered an error\n" \
                                     "3. Please check the action server logs"
                        st.warning("⚠️ Empty response from Rasa. Check action server is running on port 5055.")
                else:
                    bot_response = str(rasa_response)
                
                # Display bot response
                st.write(bot_response)
                
                # Add bot response to history
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                # Show debug info in expander
                with st.expander("🔍 Debug Info"):
                    st.json({
                        "rasa_response": rasa_response,
                        "user_message": user_input,
                        "response_length": len(rasa_response) if isinstance(rasa_response, list) else 0
                    })
                    
                    # Try to get intent prediction
                    try:
                        parse_response = requests.post(
                            f"{st.session_state.rasa_url.replace('/webhooks/rest/webhook', '/model/parse')}",
                            json={"text": user_input},
                            timeout=5
                        )
                        if parse_response.status_code == 200:
                            parse_data = parse_response.json()
                            st.json({
                                "intent_prediction": parse_data.get("intent", {}),
                                "entities": parse_data.get("entities", [])
                            })
                    except:
                        pass
                    
            except requests.exceptions.ConnectionError:
                error_msg = "❌ Cannot connect to Rasa server. Please make sure:\n1. Rasa server is running (`rasa run --enable-api`)\n2. Action server is running (`rasa run actions`)\n3. The URL is correct in the sidebar"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            except requests.exceptions.Timeout:
                error_msg = "⏱️ Request timed out. The Rasa server might be slow or unavailable."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            except Exception as e:
                error_msg = f"❌ Unexpected error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer with instructions
st.markdown("---")
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Getting Started
    
    1. **Start Rasa Services:**
       ```bash
       # Terminal 1 - Action Server
       conda activate hybrid_gemini_assistant
       rasa run actions
       
       # Terminal 2 - Rasa Server
       rasa run --enable-api
       ```
    
    2. **Run Streamlit App:**
       ```bash
       streamlit run app/streamlit_app.py
       ```
    
    3. **Check Connection:**
       - Click "Check Rasa Connection" in the sidebar
       - Make sure status shows "Connected"
    
    4. **Start Chatting:**
       - Type your message or click an example query
       - The bot will respond using Rasa + Gemini
    
    ### Banking Features
    
    - **Check Balance:** "What is my checking account balance?"
    - **Transactions:** "Show me my recent transactions"
    - **Spending Analysis:** "Analyze my spending patterns"
    - **Transfers:** "Transfer 500 dollars from checking to savings"
    - **Banking Questions:** "What is overdraft protection?"
    
    ### Troubleshooting
    
    - If you get "Cannot connect" errors, verify Rasa is running
    - Check the Debug Info expander to see raw Rasa responses
    - Make sure GEMINI_API_KEY is set for fallback responses
    """)

# Display system info
with st.expander("ℹ️ System Information"):
    st.json({
        "Rasa URL": st.session_state.rasa_url,
        "Messages in History": len(st.session_state.messages),
        "Connection Status": st.session_state.api_status,
        "Gemini API Key": "Set" if os.getenv("GEMINI_API_KEY") else "Not Set"
    })

