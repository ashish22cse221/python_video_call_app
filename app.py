import streamlit as st
import numpy as np
import cv2
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from datetime import datetime
import threading
import json
import os
from pathlib import Path

# Create a data directory if it doesn't exist
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# Custom CSS styling
st.set_page_config(
    page_title="Multi-User Video Chat",
    layout="wide"
)

# Add custom CSS with Google Fonts

# [Previous imports and setup code remains the same until the CSS section]

# Add custom CSS with Google Fonts and dark theme
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
        
        /* Dark theme background */
        .stApp {
            background-color: #1A1B1E;
            color: #E0E0E0;
        }
        
        /* Main title styling */
        .title {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            color: #7C3AED;  /* Purple accent */
            font-size: 2.5rem;
            margin-bottom: 2rem;
            text-align: center;
            text-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
        }
        
        /* Headers styling */
        .header {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            color: #E0E0E0;
            font-size: 1.5rem;
            margin: 1rem 0;
            border-bottom: 2px solid #7C3AED;
            padding-bottom: 0.5rem;
            display: inline-block;
        }
        
        /* Chat messages styling */
        .message {
            font-family: 'Inter', sans-serif;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .message-own {
            background-color: #4C1D95;  /* Darker purple for own messages */
            margin-left: 20%;
            color: #E0E0E0;
            border: 1px solid #7C3AED;
        }
        
        .message-other {
            background-color: #2D2D2D;  /* Dark gray for other messages */
            margin-right: 20%;
            color: #E0E0E0;
            border: 1px solid #404040;
        }
        
        /* User list styling */
        .user-list {
            font-family: 'Inter', sans-serif;
            padding: 1rem;
            background-color: #2D2D2D;
            border-radius: 12px;
            border: 1px solid #404040;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Form styling */
        .stTextInput > div > div > input {
            font-family: 'Inter', sans-serif;
            background-color: #2D2D2D !important;
            color: #E0E0E0 !important;
            border: 1px solid #404040 !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #7C3AED !important;
            box-shadow: 0 0 0 1px #7C3AED !important;
        }
        
        .stButton > button {
            font-family: 'Poppins', sans-serif;
            font-weight: 500;
            background-color: #7C3AED !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.5rem !important;
            border: none !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3) !important;
        }
        
        .stButton > button:hover {
            background-color: #6D28D9 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(124, 58, 237, 0.4) !important;
        }
        
        /* Sidebar styling */
        .sidebar .sidebar-content {
            font-family: 'Inter', sans-serif;
            background-color: #1A1B1E !important;
        }
        
        /* Success message styling */
        .success {
            font-family: 'Inter', sans-serif;
            color: #10B981;  /* Emerald green */
            background-color: #064E3B;  /* Dark emerald */
            padding: 0.75rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid #10B981;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Additional dark theme elements */
        .stSelectbox > div > div {
            background-color: #2D2D2D !important;
            color: #E0E0E0 !important;
        }
        
        .stMarkdown {
            color: #E0E0E0 !important;
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1A1B1E;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #4C1D95;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #7C3AED;
        }
        
        /* Video container styling */
        .stVideo {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            border: 1px solid #404040;
        }
    </style>
""", unsafe_allow_html=True)

# [Rest of the code remains the same]















# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = {}
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'room_id' not in st.session_state:
    st.session_state.room_id = ''
if 'active_users' not in st.session_state:
    st.session_state.active_users = set()

# Lock for thread-safe operations
message_lock = threading.Lock()

class VideoProcessor:
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return frame

def save_room_data(room_id, data):
    """Save room data to file"""
    file_path = DATA_DIR / f"room_{room_id}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)

def load_room_data(room_id):
    """Load room data from file"""
    file_path = DATA_DIR / f"room_{room_id}.json"
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return {'messages': [], 'users': []}

def join_room():
    """Handle room joining"""
    if not st.session_state.username or not st.session_state.room_id:
        st.markdown('<p class="header">Join a Room</p>', unsafe_allow_html=True)
        with st.form("join_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Enter your username")
            with col2:
                room_id = st.text_input("Enter room code")
            
            submit = st.form_submit_button("Join Room")
            
            if submit and username and room_id:
                st.session_state.username = username
                st.session_state.room_id = room_id
                
                # Load existing room data
                room_data = load_room_data(room_id)
                if username not in room_data['users']:
                    room_data['users'].append(username)
                    save_room_data(room_id, room_data)
                
                return True
    return bool(st.session_state.username and st.session_state.room_id)

def add_message(username, message, room_id):
    """Add a message to the chat history"""
    with message_lock:
        room_data = load_room_data(room_id)
        room_data['messages'].append({
            'username': username,
            'message': message,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        save_room_data(room_id, room_data)

def main():
    st.markdown('<h1 class="title">Multi-User Video Chat</h1>', unsafe_allow_html=True)
    
    # Join room first
    if not join_room():
        return
    
    # Display room information
    st.sidebar.markdown(f'<div class="success">Connected to Room: {st.session_state.room_id}</div>', unsafe_allow_html=True)
    
    # Load room data
    room_data = load_room_data(st.session_state.room_id)
    
    # Display active users
    st.sidebar.markdown('<p class="header">Active Users</p>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="user-list">', unsafe_allow_html=True)
    for user in room_data['users']:
        st.sidebar.markdown(f"👤 {user}", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Create two columns for video and chat
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<p class="header">Video Call</p>', unsafe_allow_html=True)
        
        # WebRTC Configuration
        rtc_config = RTCConfiguration(
            {"iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {
                    "urls": ["turn:numb.viagenie.ca"],
                    "username": "webrtc@live.com",
                    "credential": "muazkh"
                }
            ]}
        )

        # Video stream
        webrtc_ctx = webrtc_streamer(
            key=f"video-chat-{st.session_state.room_id}-{st.session_state.username}",
            video_processor_factory=VideoProcessor,
            rtc_configuration=rtc_config,
            media_stream_constraints={
                "video": True,
                "audio": True
            },
        )

    with col2:
        st.markdown('<p class="header">Chat</p>', unsafe_allow_html=True)
        
        # Chat display
        chat_container = st.container()
        with chat_container:
            # Display messages from room data
            for msg in room_data['messages']:
                timestamp = msg['timestamp']
                username = msg['username']
                message = msg['message']
                
                if username == st.session_state.username:
                    st.markdown(
                        f'<div class="message message-own">'
                        f'<strong>You</strong> ({timestamp})<br>{message}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="message message-other">'
                        f'<strong>{username}</strong> ({timestamp})<br>{message}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        # Message input
        with st.form(key="message_form", clear_on_submit=True):
            message = st.text_input("Type your message")
            send_button = st.form_submit_button("Send")
            
            if send_button and message:
                add_message(st.session_state.username, message, st.session_state.room_id)
                st.experimental_rerun()

    # Add a leave room button
    if st.sidebar.button("Leave Room"):
        # Remove user from room
        room_data = load_room_data(st.session_state.room_id)
        if st.session_state.username in room_data['users']:
            room_data['users'].remove(st.session_state.username)
            save_room_data(st.session_state.room_id, room_data)
        
        # Clear session state
        st.session_state.username = ''
        st.session_state.room_id = ''
        st.experimental_rerun()

if __name__ == "__main__":
    main()