import streamlit as st
import requests
import json
import os
import time
from typing import List, Dict, Any
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URL configuration - allow for local dev or production deployed API
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Define CSS functions
def create_loading_animation_css():
    """Add CSS for a better loading animation"""
    return """
    <style>
        /* Improve visibility of the spinner */
        .stSpinner > div {
            border-width: 3px !important;
            border-color: rgba(30, 136, 229, 0.2) !important;
            border-top-color: #1E88E5 !important;
            width: 40px !important;
            height: 40px !important;
        }
        
        /* Pulsing effect for loading info messages */
        @keyframes pulse {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }
        
        .loading-message {
            animation: pulse 1.5s infinite;
            background-color: #e1f5fe !important;
            border-left: 4px solid #1E88E5 !important;
            padding: 20px !important;
        }
        
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: #1E88E5 !important;
        }
    </style>
    """

# Page configuration
st.set_page_config(
    page_title="Audience Andy",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2196F3;
        color: white;
        border-radius: 0.5rem 0.5rem 0 0.5rem;
        align-self: flex-end;
    }
    .chat-message.assistant {
        background-color: #f0f2f6;
        border-radius: 0.5rem 0.5rem 0.5rem 0;
        align-self: flex-start;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .workflow-status {
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-bottom: 0.5rem;
    }
    h1, h2, h3 {
        color: #1E88E5;
    }
    .highlight {
        background-color: #ffeb3b;
        padding: 0.25rem;
        border-radius: 0.25rem;
    }
    .btn-primary {
        background-color: #1E88E5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Add loading animation CSS
st.markdown(create_loading_animation_css(), unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "workflow_stage" not in st.session_state:
    st.session_state.workflow_stage = "initial"
    
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False

if "product_data" not in st.session_state:
    st.session_state.product_data = None
    
if "market_data" not in st.session_state:
    st.session_state.market_data = None
    
if "categories" not in st.session_state:
    st.session_state.categories = None
    
if "audience_segments" not in st.session_state:
    st.session_state.audience_segments = None
    
if "strategies" not in st.session_state:
    st.session_state.strategies = None

# Helper functions
def get_stage_estimated_time(stage):
    """Return the estimated time for each workflow stage in seconds"""
    stage_times = {
        "initial": 5,
        "url_analysis": 20,
        "market_research": 25,
        "category_mapping": 40,
        "audience_segmentation": 20,
        "marketing_strategy": 30,
        "final_summary": 15
    }
    return stage_times.get(stage, 15)  # Default 15 seconds for unknown stages

def get_api_status():
    """Get the current status of the API workflow"""
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            # Don't show error message on every retry
            if response.status_code == 500:
                return None
            st.error(f"Error getting API status: {response.text}")
            return None
    except requests.exceptions.Timeout:
        # Silently handle timeout errors without showing the user
        return None
    except requests.exceptions.ConnectionError:
        # Silently handle connection errors without showing the user
        return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def update_session_state_from_api():
    """Update the session state based on the API status"""
    # Limit how often we check API status
    current_time = time.time()
    last_check = getattr(st.session_state, 'last_api_check', 0)
    
    # Only check once every 2 seconds to avoid spamming
    if current_time - last_check < 2:
        return
        
    st.session_state.last_api_check = current_time
    
    status_data = get_api_status()
    if status_data:
        st.session_state.workflow_stage = status_data.get("workflow_stage", "initial")
        
        # Update product data if available
        if status_data.get("product_data"):
            st.session_state.product_data = status_data["product_data"]
            
        # Update market data if available
        if status_data.get("market_data"):
            st.session_state.market_data = status_data["market_data"]
            
        # Update categories if available
        if status_data.get("categories"):
            st.session_state.categories = status_data["categories"]
            
        # Update audience segments if available
        if status_data.get("audience_segments"):
            st.session_state.audience_segments = status_data["audience_segments"]
            
        # Update strategies if available
        if status_data.get("strategies"):
            st.session_state.strategies = status_data["strategies"]

def start_conversation():
    """Start a new conversation with the assistant"""
    
    # Add a visible loading message
    loading_msg = st.empty()
    loading_msg.info("Starting conversation...")
    
    # Prevent repeated calls in a short time period
    current_time = time.time()
    last_start_attempt = getattr(st.session_state, 'last_start_attempt', 0)
    
    # Only attempt to start once every 5 seconds
    if current_time - last_start_attempt < 5:
        loading_msg.warning("Please wait a moment before trying again.")
        return False
        
    st.session_state.last_start_attempt = current_time
    
    try:
        # Make sure messages list exists
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Show the actual URL being called for debugging
        api_url = f"{API_URL}/api/start"
        st.session_state.debug_info = f"Calling: {api_url}"
        
        # Log the request details
        loading_msg.info(f"Sending request to {api_url}...")
        
        response = requests.post(api_url, timeout=10)  # Increased timeout
        
        # Log the raw response for debugging
        st.session_state.raw_response = {
            "status_code": response.status_code,
            "content_type": response.headers.get('Content-Type', 'unknown'),
            "content_length": len(response.content),
            "raw_text": response.text[:500]  # First 500 chars
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                # Clear any previous error flags
                st.session_state.connection_error_shown = False
                st.session_state.timeout_error_shown = False
                st.session_state.server_error_shown = False
                
                # Log the received message for debugging
                message = data.get("message", "No message in response")
                st.session_state.debug_message = message
                
                if not message:
                    loading_msg.error("API returned success but no message content!")
                    return False
                
                # Add the message to the chat history
                st.session_state.messages.append({"role": "assistant", "content": message})
                
                # Verify message was added
                st.session_state.message_count = len(st.session_state.messages)
                
                update_session_state_from_api()
                loading_msg.success("Conversation started successfully!")
                return True
            except json.JSONDecodeError as e:
                loading_msg.error(f"Invalid JSON response: {str(e)}")
                st.session_state.json_error = str(e)
                return False
        elif response.status_code == 500:
            # Handle server error with more visible feedback
            loading_msg.error(f"Server error: {response.text}")
            st.session_state.server_error_shown = True
            return False
        else:
            # Show the actual error for better debugging
            loading_msg.error(f"Error starting conversation: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError as e:
        loading_msg.error(f"Cannot connect to the server at {API_URL}. Please check if the backend is running. Error: {str(e)}")
        st.session_state.connection_error_shown = True
        return False
    except requests.exceptions.Timeout:
        loading_msg.error(f"Request to {API_URL} timed out. The server might be starting up or under heavy load.")
        st.session_state.timeout_error_shown = True
        return False
    except Exception as e:
        loading_msg.error(f"Unexpected error: {str(e)}")
        st.session_state.last_error = str(e)
        return False

def send_message(message):
    """Send a message to the API and receive a response"""
    if not message.strip():
        return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Show a loading indicator in the UI
    st.session_state.is_analyzing = True
    
    try:
        # Add a progress indicator at the top of the page for URL analysis 
        if "http" in message and st.session_state.workflow_stage == "initial":
            progress_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0)
            status_placeholder = st.empty()
            status_placeholder.write("Starting comprehensive product analysis. This typically takes 1-2 minutes.")
            
            # Total estimated time for all workflow stages
            total_time = sum(get_stage_estimated_time(stage) for stage in ["url_analysis", "market_research", "category_mapping", "audience_segmentation", "marketing_strategy", "final_summary"])
            
            start_time = time.time()
            
            # Simulate progress for long-running requests
            def update_progress():
                # Create realistic progress based on estimated times for each stage
                stages = [
                    ("url_analysis", 0.15),
                    ("market_research", 0.25), 
                    ("category_mapping", 0.40),
                    ("audience_segmentation", 0.60),
                    ("marketing_strategy", 0.85),
                    ("final_summary", 1.0)
                ]
                
                current_progress = 0.0
                last_update = time.time()
                is_analyzing = True
                
                try:
                    while current_progress < 0.99 and is_analyzing:
                        # Check if session_state still exists and has the attribute
                        try:
                            is_analyzing = st.session_state.get("is_analyzing", False)
                        except:
                            # If we can't access session_state, assume we should stop
                            is_analyzing = False
                            break
                            
                        current_time = time.time()
                        elapsed = current_time - start_time
                        
                        # Don't update too frequently to avoid flickering
                        if current_time - last_update < 1.0:
                            time.sleep(0.5)
                            continue
                        
                        # Calculate progress based on elapsed time
                        current_progress = min(0.99, elapsed / total_time)
                        
                        try:
                            progress_bar.progress(current_progress)
                            
                            # Update the status message with estimated time remaining
                            remaining = max(0, total_time - elapsed)
                            status_placeholder.write(f"Analyzing product... (Approximately {int(remaining)} seconds remaining)")
                        except:
                            # If UI elements are no longer accessible, exit the loop
                            break
                        
                        last_update = current_time
                        time.sleep(1)
                    
                    # Try to clear the progress elements when done
                    try:
                        progress_placeholder.empty()
                        status_placeholder.empty()
                    except:
                        # If UI elements are no longer accessible, just continue
                        pass
                        
                except Exception as e:
                    # Catch any other errors to prevent thread crashes
                    print(f"Error in progress thread: {str(e)}")
                    
            # Start progress update in a separate thread
            import threading
            thread = threading.Thread(target=update_progress)
            thread.daemon = True  # Make sure the thread doesn't block app exit
            thread.start()
        
        # Send the message to the API
        response = requests.post(
            f"{API_URL}/api/message",
            json={"message": message}
        )
        
        # Always set is_analyzing to False when done, whether success or failure
        st.session_state.is_analyzing = False
        
        if response.status_code == 200:
            data = response.json()
            # Add assistant response to chat
            st.session_state.messages.append({"role": "assistant", "content": data["message"]})
            # Update session state from API
            update_session_state_from_api()
        else:
            st.error(f"Error sending message: {response.text}")
            st.session_state.messages.append({"role": "assistant", "content": f"I'm sorry, there was an error processing your message. Please try again."})
    except Exception as e:
        # Make sure we set is_analyzing to False even if we have an exception
        st.session_state.is_analyzing = False
        st.error(f"Error connecting to API: {str(e)}")
        st.session_state.messages.append({"role": "assistant", "content": f"I'm sorry, there was an error connecting to the service. Please check your connection and try again."})

def display_chat():
    """Display the chat messages"""
    # Add explicit debug for message count
    message_count = len(st.session_state.get("messages", []))
    
    # Debug container at the top
    debug_expander = st.expander("Chat Debug Info (Expand to view)")
    with debug_expander:
        st.write(f"Messages in state: {message_count}")
        st.write(f"Current workflow stage: {st.session_state.get('workflow_stage', 'unknown')}")
        st.write(f"Is analyzing: {st.session_state.get('is_analyzing', False)}")
        
        if message_count > 0:
            st.write("Last message:")
            st.json(st.session_state.messages[-1])
        else:
            st.write("No messages found in session state!")
    
    # Display messages with better error handling
    if message_count > 0:
        for i, message in enumerate(st.session_state.messages):
            role = message.get("role", "unknown")
            content = message.get("content", "No content")
            
            with st.chat_message(role):
                st.write(content)
    else:
        st.warning("No messages to display. Try clicking 'Start Conversation' again.")
    
    # Display the loading indicator if we're analyzing
    if st.session_state.is_analyzing:
        with st.chat_message("assistant"):
            # Show context-specific loading messages based on the workflow stage
            current_stage = st.session_state.workflow_stage
            est_time = get_stage_estimated_time(current_stage)
            
            if current_stage == "initial" or current_stage == "url_analysis":
                st.markdown(f'<div class="loading-message">🔍 Analyzing product URL and extracting data... (Est. time: {est_time} seconds)</div>', unsafe_allow_html=True)
            elif current_stage == "market_research":
                st.markdown(f'<div class="loading-message">📊 Researching market data and identifying competitors... (Est. time: {est_time} seconds)</div>', unsafe_allow_html=True)
            elif current_stage == "category_mapping":
                st.markdown(f'<div class="loading-message">🗂️ Mapping product to marketing categories and exploring subcategories... (Est. time: {est_time} seconds)</div>', unsafe_allow_html=True)
            elif current_stage == "audience_segmentation":
                st.markdown(f'<div class="loading-message">👥 Generating detailed audience segments based on product analysis... (Est. time: {est_time} seconds)</div>', unsafe_allow_html=True)
            elif current_stage == "marketing_strategy":
                st.markdown(f'<div class="loading-message">📈 Developing marketing strategy recommendations... (Est. time: {est_time} seconds)</div>', unsafe_allow_html=True)
            elif current_stage == "final_summary":
                st.markdown(f'<div class="loading-message">📑 Creating comprehensive analysis summary... (Est. time: {est_time} seconds)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="loading-message">⏳ Processing your request...</div>', unsafe_allow_html=True)
            
            # Add a spinner to indicate ongoing processing
            with st.spinner(""):
                # This empty container just ensures the spinner stays visible
                st.empty()

def display_workflow_status():
    """Display the current workflow status"""
    stages = {
        "initial": "Initial",
        "url_analysis": "Product Analysis",
        "market_research": "Market Research",
        "category_mapping": "Category Mapping",
        "audience_segmentation": "Audience Segmentation",
        "marketing_strategy": "Marketing Strategy",
        "final_summary": "Final Summary"
    }
    
    current_stage = st.session_state.workflow_stage
    
    st.sidebar.subheader("Workflow Status")
    
    for stage, label in stages.items():
        if stage == current_stage:
            st.sidebar.markdown(f"**→ {label}** 🔍")
        elif stages_completed(stage, current_stage):
            st.sidebar.markdown(f"✅ {label}")
        else:
            st.sidebar.markdown(f"⬜ {label}")

def stages_completed(stage, current_stage):
    """Check if a stage is completed based on the current stage"""
    stage_order = [
        "initial", 
        "url_analysis", 
        "market_research", 
        "category_mapping", 
        "audience_segmentation", 
        "marketing_strategy", 
        "final_summary"
    ]
    
    if stage == current_stage:
        return False
    
    stage_idx = stage_order.index(stage)
    current_idx = stage_order.index(current_stage)
    
    return stage_idx < current_idx

def display_basic_data():
    """Display basic data in the sidebar"""
    if not st.session_state.product_data and not st.session_state.audience_segments:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Analysis Status")
    
    # Basic product info
    if st.session_state.product_data:
        product_data = st.session_state.product_data
        st.sidebar.markdown(f"**Product:** {product_data.get('title', 'N/A')}")
    
    # Basic audience segments info
    if st.session_state.audience_segments:
        segments = st.session_state.audience_segments
        segments_names = [segment.get('name', 'Unknown') for segment in segments]
        st.sidebar.markdown(f"**Identified segments:** {len(segments_names)}")
    
    # Basic strategies info
    if st.session_state.strategies:
        strategies = st.session_state.strategies
        st.sidebar.markdown(f"**Marketing strategies:** {len(strategies)}")

    # Hint for how to continue
    if st.session_state.workflow_stage == "final_summary":
        st.sidebar.markdown("---")
        st.sidebar.info("💡 You can now ask questions about any part of the analysis or start a new analysis.")

def reset_conversation():
    """Reset the conversation and workflow"""
    try:
        response = requests.post(f"{API_URL}/api/reset")
        if response.status_code == 200:
            # Clear session state
            st.session_state.messages = []
            st.session_state.workflow_stage = "initial"
            st.session_state.product_data = None
            st.session_state.market_data = None
            st.session_state.categories = None
            st.session_state.audience_segments = None
            st.session_state.strategies = None
            # Start a new conversation
            start_conversation()
        else:
            st.error(f"Error resetting conversation: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

# Main app layout
st.title("🎯 Audience Andy")
st.markdown("### AI-Powered Audience Segmentation & Marketing Strategy Assistant")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=Audience+Andy", width=150)
    st.markdown("## Audience Andy")
    st.markdown("Analyze products and identify target audiences for marketing.")
    
    st.button("New Analysis", on_click=reset_conversation)
    
    # Display workflow status
    display_workflow_status()
    
    # Display basic data
    display_basic_data()

# Main content area - only chat interface
st.subheader("Chat with Audience Andy")

# Display the chat interface
chat_container = st.container()

with chat_container:
    # If no conversation has started yet, show a welcome message
    if not st.session_state.messages:
        st.info("""
        👋 Welcome to Audience Andy!
        
        I can help you analyze products to identify target audiences and develop marketing strategies.
        
        To get started:
        1. Share a product URL and ask me to analyze it
        2. I'll break down audience segments and suggest marketing approaches
        3. You can ask follow-up questions about any part of the analysis
        
        Press "Start Conversation" below to begin!
        """)
        
        # Add a button to start the conversation only when the user is ready
        if st.button("Start Conversation"):
            # Show debug section
            debug_container = st.container()
            
            # Call start_conversation and display debug info
            success = start_conversation()
            
            # Display debugging information
            with debug_container:
                st.markdown("---")
                with st.expander("Debug Information"):
                    st.write("Debug Info:", st.session_state.get("debug_info", "No debug info"))
                    st.write("API URL:", API_URL)
                    st.write("Initial Message:", st.session_state.get("debug_message", "No message received"))
                    st.write("Connection Error:", st.session_state.get("connection_error_shown", False))
                    st.write("Timeout Error:", st.session_state.get("timeout_error_shown", False))
                    st.write("Server Error:", st.session_state.get("server_error_shown", False))
                    st.write("Message Count:", len(st.session_state.get("messages", [])))
                    if st.session_state.get("messages"):
                        st.write("Latest Message:", st.session_state.messages[-1])
            
            # Only rerun if we successfully started the conversation
            if success:
                st.rerun()
            else:
                st.warning("Could not start conversation. Check debug information for details.")
    else:
        # Only display chat if we have messages
        display_chat()
        
        # Only show chat input when we have a conversation started
        user_input = st.chat_input("Type your message here...")
        if user_input:
            send_message(user_input)
            st.rerun() 