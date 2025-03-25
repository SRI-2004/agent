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
        
        /* Loading message styling */
        .loading-message {
            animation: pulse 1.5s infinite;
            background-color: #f8f9fa !important;
            border-left: 4px solid #1E88E5 !important;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 2px;
        }
        
        /* Add CSS for the rest of your loading elements */
        """ + create_thinking_animation_css() + create_ui_style_css() + """
    </style>
    """

def create_thinking_animation_css():
    """Create CSS specifically for the thinking animation"""
    return """
        /* Animated thinking dots */
        @keyframes thinking-dots {
            0% { content: "."; }
            33% { content: ".."; }
            66% { content: "..."; }
            100% { content: ""; }
        }
        
        .thinking-animation {
            display: flex;
            align-items: center;
            margin: 10px 0;
            padding: 12px 16px;
            background-color: #1e293b;
            border-radius: 18px 18px 18px 0;
            color: white;
            font-weight: 500;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            max-width: fit-content;
            position: relative;
        }
        
        .thinking-animation::after {
            content: "";
            display: inline-block;
            animation: thinking-dots 1.5s infinite;
            margin-left: 4px;
            font-weight: bold;
        }
    """

def create_ui_style_css():
    """Create CSS for UI elements like chat container, sidebar, etc."""
    return """
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: #1E88E5 !important;
        }
        
        /* Dropdown styling */
        .category-dropdown {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 10px;
        }
        
        /* Tree view for subcategories */
        .tree-view {
            margin-left: 20px;
            border-left: 1px solid #334155;
            padding-left: 15px;
        }
        
        .tree-node {
            margin: 6px 0;
            padding: 5px;
            border-radius: 4px;
            background-color: #1e293b;
            color: #ffffff !important;
        }
        
        /* Fixed bottom input area with integrated style */
        .fixed-bottom-container {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            background-color: #fff !important;
            border-top: 1px solid #e0e0e0 !important;
            padding: 16px 32px !important;
            z-index: 9999 !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0px -2px 10px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* Adjust content to not be hidden behind fixed bottom */
        .main-content {
            padding-bottom: 80px !important; /* Ensure content isn't hidden behind fixed bottom */
            margin-bottom: 20px !important;
        }
        
        /* Style for the integrated input box */
        .input-container {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            max-width: 1200px !important;
            margin: 0 auto !important;
            background-color: #f8f9fa !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        /* Style for the new analysis button part of the container */
        .new-analysis-btn {
            background-color: #1e293b !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            cursor: pointer !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            min-width: 130px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        /* Style for the input field part */
        .input-field {
            flex-grow: 1 !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
        }
        
        /* Hide streamlit branding */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        /* Make sure chat messages container has enough space */
        .chat-container {
            padding-bottom: 100px !important; /* Extra padding to account for fixed bottom bar */
            max-height: calc(100vh - 220px) !important; /* Adjust for fixed elements */
            overflow-y: auto !important;
        }
        
        /* Force user messages to right side */
        [data-testid="stChatInput"] {
            width: 100% !important;
            border: none !important;
            background: transparent !important;
        }
        
        /* Force chat input to fill the container */
        [data-testid="stChatInput"] > div {
            width: 100% !important;
            padding: 0 !important;
            background: transparent !important;
        }

        /* The trick to align messages correctly */
        [data-testid="stChatMessageContainer"] {
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        [data-testid="stChatMessage-user"] {
            align-self: flex-end !important; 
            background-color: #1E88E5 !important;
            color: white !important;
            border-radius: 18px 18px 0 18px !important;
            margin-left: auto !important;
            margin-right: 0 !important;
        }
        
        [data-testid="stChatMessage-assistant"] {
            align-self: flex-start !important;
            background-color: #1e293b !important;
            color: white !important;
            border-radius: 18px 18px 18px 0 !important;
            margin-left: 0 !important;
            margin-right: auto !important;
        }
        
        /* Sidebar refinements with dark color */
        [data-testid="stSidebar"] {
            background-color: #101828 !important; /* Dark background */
            border-right: 1px solid #222;
        }
        
        /* Sidebar expander styling */
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            border: 1px solid #334155 !important;
            background-color: #1e293b !important;
            border-radius: 4px !important;
            margin-bottom: 10px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stExpander"] > details {
            background-color: #1e293b !important;
            color: #ffffff !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stExpander"] > details > summary {
            background-color: #1e293b !important;
            color: #ffffff !important;
            padding: 10px !important;
            border-radius: 4px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stExpander"] > details > summary:hover {
            background-color: #334155 !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stExpander"] > details > div {
            padding: 10px !important;
            background-color: #1e293b !important;
        }
        
        /* Header styling */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 500 !important;
            color: #263238 !important; /* Darker text for headers in main content */
        }
        
        /* Sidebar header styling */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, 
        [data-testid="stSidebar"] h5, 
        [data-testid="stSidebar"] h6 {
            color: #ffffff !important; /* White text for headers in sidebar */
        }
        
        /* Button styling */
        button[kind="primary"] {
            background-color: #1E88E5 !important;
            color: white !important;
        }
        
        /* Status indicators */
        .status-complete {
            color: #4ade80 !important; /* Brighter green for dark background */
        }
        
        .status-current {
            color: #60a5fa !important; /* Brighter blue for dark background */
            font-weight: 500;
        }
        
        .status-pending {
            color: #94a3b8 !important; /* Lighter gray for dark background */
        }
        
        /* General text color improvements for light mode (main content) */
        p, span, div, label, li {
            color: #263238 !important; /* Dark gray for better readability */
        }
        
        /* Ensure sidebar text is white */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] a {
            color: #ffffff !important;
        }
        
        /* Category and segment items */
        .category-item, .segment-item {
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 4px;
            background-color: #1e293b;
            color: #ffffff !important;
        }
        
        /* Make info messages more readable */
        .stAlert p {
            color: #263238 !important;
        }
        
        /* Sidebar divider styling */
        [data-testid="stSidebar"] hr {
            border-color: #334155 !important;
            margin: 20px 0 !important;
        }
    """

# Page configuration
st.set_page_config(
    page_title="Audience Andy",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown(create_loading_animation_css(), unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "workflow_stage" not in st.session_state:
    st.session_state.workflow_stage = "initial"
    
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False

if "thinking_animation_type" not in st.session_state:
    st.session_state.thinking_animation_type = "auto"

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

if "expanded_categories" not in st.session_state:
    st.session_state.expanded_categories = {}
    
if "expanded_segments" not in st.session_state:
    st.session_state.expanded_segments = {}

# Helper functions to handle dropdown clicks
def toggle_category(category_id):
    st.session_state.expanded_categories[category_id] = not st.session_state.expanded_categories.get(category_id, False)

def toggle_segment(segment_id):
    st.session_state.expanded_segments[segment_id] = not st.session_state.expanded_segments.get(segment_id, False)

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

def display_thinking_animation():
    """Display a thinking animation with stage-specific loading messages"""
    # Show the basic thinking animation bubble
    st.markdown('<div class="thinking-animation">Thinking</div>', unsafe_allow_html=True)
    
    # Show more detailed message about what's happening based on the current stage
    current_stage = st.session_state.workflow_stage
    est_time = get_stage_estimated_time(current_stage)
    
    with st.chat_message("assistant"):
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
            # This empty container ensures the spinner stays visible
            st.empty()

def display_simple_thinking_animation():
    """Display just the thinking animation bubble without additional messages"""
    st.markdown('<div class="thinking-animation">Thinking</div>', unsafe_allow_html=True)

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

def send_message(message, thinking_animation_type="auto"):
    """Send a message to the API and receive a response
    
    Args:
        message: The message text to send
        thinking_animation_type: The type of thinking animation to show
            - "auto": Choose based on workflow stage (default)
            - "simple": Only show the basic thinking bubble
            - "detailed": Show the thinking bubble with detailed stage info
            - "none": Don't show any thinking animation
    """
    if not message.strip():
        return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Show a loading indicator in the UI based on the specified animation type
    if thinking_animation_type != "none":
        st.session_state.is_analyzing = True
        
        # Store the animation type for display_chat to use
        st.session_state.thinking_animation_type = thinking_animation_type
    
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
    """Display the chat messages in a chat-like interface"""
    # Add explicit debug for message count
    message_count = len(st.session_state.get("messages", []))
    
    # Debug container at the top - hidden by default in professional mode
    debug_expander = st.expander("Debug Info", expanded=False)
    with debug_expander:
        st.write(f"Messages in state: {message_count}")
        st.write(f"Current workflow stage: {st.session_state.get('workflow_stage', 'unknown')}")
        st.write(f"Is analyzing: {st.session_state.get('is_analyzing', False)}")
        
        if message_count > 0:
            st.write("Last message:")
            st.json(st.session_state.messages[-1])
        else:
            st.write("No messages found in session state!")
    
    # Create a container with the appropriate bottom padding
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display messages with better error handling
    if message_count > 0:
        for i, message in enumerate(st.session_state.messages):
            role = message.get("role", "unknown")
            content = message.get("content", "No content")
            
            with st.chat_message(role):
                st.write(content)
    else:
        st.info("No messages to display. Start the conversation by entering a message below.")
    
    # Display the "Thinking..." animation when analyzing
    if st.session_state.is_analyzing:
        animation_type = st.session_state.get("thinking_animation_type", "auto")
        
        if animation_type == "simple":
            # Always use simple animation
            display_simple_thinking_animation()
        elif animation_type == "detailed":
            # Always use detailed animation with stage info
            display_thinking_animation()
        elif animation_type == "auto":
            # Auto choose based on workflow stage
            if st.session_state.workflow_stage != "initial":
                display_thinking_animation()
            else:
                display_simple_thinking_animation()
        # If animation_type is "none", we don't show anything (but this case shouldn't occur here)
            
    st.markdown('</div>', unsafe_allow_html=True)

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
    
    st.sidebar.markdown("### Workflow Status")
    
    for stage, label in stages.items():
        if stage == current_stage:
            st.sidebar.markdown(f'<div class="status-current">→ {label} 🔍</div>', unsafe_allow_html=True)
        elif stages_completed(stage, current_stage):
            st.sidebar.markdown(f'<div class="status-complete">✓ {label}</div>', unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f'<div class="status-pending">□ {label}</div>', unsafe_allow_html=True)

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

def display_categories_as_dropdown():
    """Display categories as a dropdown with tree structure for subcategories"""
    if not st.session_state.categories:
        return
    
    categories = st.session_state.categories
    st.sidebar.markdown("### Product Categories")
    
    for i, category in enumerate(categories):
        category_id = f"category_{i}"
        
        # Add type checking to handle different category data structures
        if isinstance(category, dict):
            category_name = category.get('name', 'Unknown')
            subcategories = category.get('subcategories', [])
        elif isinstance(category, str):
            category_name = category
            subcategories = []
        else:
            # Handle unexpected types
            category_name = f"Category {i+1}"
            subcategories = []
        
        # Use true Streamlit expander with custom styling
        if subcategories:
            with st.sidebar.expander(f"📂 {category_name}", expanded=st.session_state.expanded_categories.get(category_id, False)):
                # Display subcategories in a tree structure
                for j, subcategory in enumerate(subcategories):
                    # Handle subcategories that might be strings or dicts
                    if isinstance(subcategory, dict) and 'name' in subcategory:
                        subcategory_name = subcategory['name']
                    else:
                        subcategory_name = str(subcategory)
                    
                    # Display with tree-like indentation
                    st.markdown(f'<div class="tree-node">└── {subcategory_name}</div>', unsafe_allow_html=True)
        else:
            # Just show the category name if no subcategories
            st.sidebar.markdown(f'<div class="category-item">📄 {category_name}</div>', unsafe_allow_html=True)

def display_audience_segments():
    """Display audience segments as proper dropdowns with tree structure"""
    if not st.session_state.audience_segments:
        return
    
    segments = st.session_state.audience_segments
    st.sidebar.markdown("### Audience Segments")
    
    for i, segment in enumerate(segments):
        segment_id = f"segment_{i}"
        
        # Add type checking for segments too
        if isinstance(segment, dict):
            segment_name = segment.get('name', 'Unknown')
            characteristics = segment.get('characteristics', [])
        elif isinstance(segment, str):
            segment_name = segment
            characteristics = []
        else:
            segment_name = f"Segment {i+1}"
            characteristics = []
        
        # Use true Streamlit expander with custom styling
        if characteristics:
            with st.sidebar.expander(f"👥 {segment_name}", expanded=st.session_state.expanded_segments.get(segment_id, False)):
                # Display characteristics in a tree structure
                for j, characteristic in enumerate(characteristics):
                    # Handle characteristics that might be strings or dicts
                    if isinstance(characteristic, dict) and 'description' in characteristic:
                        char_text = characteristic['description']
                    else:
                        char_text = str(characteristic)
                    
                    # Display with tree-like indentation and style
                    st.markdown(f'<div class="tree-node">└── {char_text}</div>', unsafe_allow_html=True)
        else:
            # Just show the segment name if no characteristics
            st.sidebar.markdown(f'<div class="segment-item">👤 {segment_name}</div>', unsafe_allow_html=True)

def display_basic_data():
    """Display basic data in the sidebar with professional styling"""
    if st.session_state.workflow_stage == "initial":
        return
    
    st.sidebar.markdown("---")
    
    # Basic product info
    if st.session_state.product_data:
        product_data = st.session_state.product_data
        st.sidebar.markdown("### Product Summary")
        st.sidebar.markdown(f"**Product:** {product_data.get('title', 'N/A')}")
        if 'price' in product_data:
            st.sidebar.markdown(f"**Price:** {product_data.get('price', 'N/A')}")
    
    # Display categories in a dropdown format
    display_categories_as_dropdown()
    
    # Display audience segments in a structured way
    display_audience_segments()
    
    # Basic strategies info
    if st.session_state.strategies:
        strategies = st.session_state.strategies
        st.sidebar.markdown("### Marketing Strategies")
        st.sidebar.markdown(f"**Available strategies:** {len(strategies)}")
        for i, strategy in enumerate(strategies):
            if isinstance(strategy, dict) and 'name' in strategy:
                st.sidebar.markdown(f"• {strategy['name']}")
            elif isinstance(strategy, str):
                st.sidebar.markdown(f"• Strategy {i+1}")

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
            st.session_state.is_analyzing = False
            st.session_state.thinking_animation_type = "auto"
            st.session_state.product_data = None
            st.session_state.market_data = None
            st.session_state.categories = None
            st.session_state.audience_segments = None
            st.session_state.strategies = None
            st.session_state.expanded_categories = {}
            st.session_state.expanded_segments = {}
            # Start a new conversation
            start_conversation()
        else:
            st.error(f"Error resetting conversation: {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

# Main app layout - clean and professional
st.markdown("# Audience Andy")
st.markdown("##### AI-Powered Audience Segmentation & Marketing Strategy")

# Sidebar - clean, professional look
with st.sidebar:
    # Use a more professional logo placeholder
    st.image("/home/srinivasan/FIles/frontend/agent/Group.png", width=150)
    st.markdown("---")
    
    # Display workflow status
    display_workflow_status()
    
    # Display structured data
    display_basic_data()

# Main content area - only chat interface
chat_container = st.container()

with chat_container:
    # If no conversation has started yet, show a welcome message
    if not st.session_state.messages:
        st.markdown("""
        ### Welcome to Audience Andy
        
        I can help you analyze products to identify target audiences and develop marketing strategies.
        
        To get started:
        1. Share a product URL and ask me to analyze it
        2. I'll break down audience segments and suggest marketing approaches
        3. You can ask follow-up questions about any part of the analysis
        """)
        
        # Add a button to start the conversation only when the user is ready
        if st.button("Start Conversation", use_container_width=False):
            # Debug section hidden by default
            debug_container = st.expander("Debug Information", expanded=False)
            
            # Call start_conversation and display debug info
            success = start_conversation()
            
            # Display debugging information
            with debug_container:
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
        
        # Create a fixed bottom container that holds both elements
        st.markdown('<div class="fixed-bottom-container">', unsafe_allow_html=True)
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        
        # Create columns inside the fixed container for the button and input
        cols = st.columns([1, 6])
        
        # New Analysis button in the first column
        with cols[0]:
            if st.button("New Analysis", key="new_analysis_bottom", use_container_width=True):
                reset_conversation()
                st.rerun()
        
        # Chat input in the second column
        with cols[1]:
            user_input = st.chat_input("Type your message here...")
            if user_input:
                # Choose the thinking animation type based on message content
                if "http" in user_input and st.session_state.workflow_stage == "initial":
                    # For URL analysis, use detailed animation
                    animation_type = "detailed"
                elif any(keyword in user_input.lower() for keyword in ["quick", "fast", "simple", "quick question"]):
                    # For quick questions, use simple animation
                    animation_type = "simple"
                elif any(keyword in user_input.lower() for keyword in ["analyze", "research", "explore", "investigate"]):
                    # For analytical questions, use detailed animation
                    animation_type = "detailed"
                else:
                    # Default to automatic behavior
                    animation_type = "auto"
                    
                send_message(user_input, thinking_animation_type=animation_type)
                st.rerun()
        
        # Close the container divs
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True) 