import streamlit as st
from google import genai
import os

# --- 1. SETUP API ---
def get_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return None

# --- 2. LOAD KNOWLEDGE ---
@st.cache_data(show_spinner=False)
def get_project_context():
    combined_text = ""
    # Ensure these exist!
    files_to_read = [
        "DASHBOARD_COMPLETE_GUIDE.md",
        "EXECUTIVE_SUMMARY.md", 
        "PROBLEM_STATEMENT_AND_APPROACH.md"
    ]
    for filename in files_to_read:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                combined_text += f"\n\n--- SOURCE: {filename} ---\n{f.read()}"
    return combined_text


# --- 3. MAIN CHATBOT FUNCTION ---
@st.fragment
def display_chatbot():
    api_key = get_api_key()
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I analyze your dashboard data. Ask me anything."}]

    # --- THE FLOATING BUBBLE ---
    with st.popover("🗨️", use_container_width=False):
        st.markdown("### 🤖 UIDAI Assistant")
        
        # Chat History
        messages_container = st.container(height=300)
        with messages_container:
            for msg in st.session_state.messages:
                bg = "#e6f3ff" if msg["role"] == "user" else "#f0f0f0"
                align = "right" if msg["role"] == "user" else "left"
                st.markdown(f"<div style='text-align: {align}; background-color: {bg}; padding: 8px; border-radius: 8px; margin-bottom: 5px; color: black;'>{msg['content']}</div>", unsafe_allow_html=True)

        # Input
        if prompt := st.chat_input("Ask...", key="floating_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    # --- AI LOGIC ---
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("Thinking..."):
            context = get_project_context()
            last_q = st.session_state.messages[-1]["content"]
            try:
                if not api_key:
                    st.error("Missing GEMINI_API_KEY in secrets.")
                    return

                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=f"Context: {context}\n\nUser Question: {last_q}\nAnswer (short):"
                )
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # --- CSS OVERLAY (FIXED CIRCLE) ---
    st.markdown("""
    <style>
    /* 1. FORCE THE CONTAINER to stay small */
    div[data-testid="stPopover"] {
        position: fixed !important;
        bottom: 30px !important;
        left: 30px !important;
        width: auto !important; /* Prevents full-width strip */
        height: auto !important;
        z-index: 999999 !important;
    }

    /* 2. FORCE THE BUTTON to be a circle */
    div[data-testid="stPopover"] > button {
        width: 60px !important;     /* Fixed width */
        height: 60px !important;    /* Fixed height */
        border-radius: 50% !important; /* Perfect circle */
        background-color: #003366 !important;
        color: white !important;
        border: 2px solid #D4AF37 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        padding: 0 !important;      /* Remove default padding */
        font-size: 28px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. HOVER EFFECT */
    div[data-testid="stPopover"] > button:hover {
        background-color: #004080 !important;
        transform: scale(1.1);
        border-color: #FFD700 !important;
    }

    /* 4. CHAT WINDOW POSITIONING */
    div[data-testid="stPopoverBody"] {
        bottom: 100px !important;
        left: 30px !important;
        width: 350px !important;
        max-height: 500px !important;
        border: 2px solid #003366 !important;
        border-radius: 12px !important;
        z-index: 999999 !important;
        position: fixed !important; /* Ensure the box stays fixed too */
    }
    </style>
    """, unsafe_allow_html=True)