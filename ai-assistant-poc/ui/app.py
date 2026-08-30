# pyrefly: ignore [missing-import]
import streamlit as st
import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Enterprise AI Assistant Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .agent-box {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏦 Commercial Bank - AI Assistant Platform")

# Session State Initialization
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_activity" not in st.session_state:
    st.session_state.last_activity = {}

# Sidebar Authentication
with st.sidebar:
    st.header("🔐 User Authentication")
    if not st.session_state.token:
        username = st.selectbox("Select Role / User", ["alice", "bob", "carol"], 
                                format_func=lambda x: f"{x.capitalize()} ({'Viewer' if x=='alice' else 'Analyst' if x=='bob' else 'Admin'})")
        password_input = st.text_input("Password", type="password", value="viewer123" if username=="alice" else "analyst123" if username=="bob" else "admin123")
        
        if st.button("Login"):
            try:
                res = requests.post(f"{API_BASE_URL}/auth/token", data={"username": username, "password": password_input})
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Authentication failed.")
            except Exception as e:
                st.error(f"Server connection error: {e}")
    else:
        st.success(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()

# Layout: 2 Columns (Left: Chat Window | Right: Agent Activity Panel)
col_chat, col_panel = st.columns([3, 2])

# --- LEFT COLUMN: CHAT INTERFACE ---
with col_chat:
    st.subheader("💬 Multi-Turn Chat Interface")
    
    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    # Input field
    if user_input := st.chat_input("Ask a question about bank policies, runbooks, or outage reports..."):
        if not st.session_state.token:
            st.error("Please log in using the sidebar first.")
        else:
            # Append user query
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
                
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            payload = {"messages": st.session_state.messages}
            
            with st.chat_message("assistant"):
                with st.spinner("Processing request through LangGraph agents..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/chat/completions", json=payload, headers=headers)
                        if res.status_code == 200:
                            data = res.json()
                            bot_response = data.get("response", "No response generated.")
                            st.write(bot_response)
                            st.session_state.messages.append({"role": "assistant", "content": bot_response})
                            
                            # Capture activity details for the right panel
                            st.session_state.last_activity = {
                                "role": data.get("user_role"),
                                "summary": data.get("execution_summary", {}),
                                "status": "Success"
                            }
                            st.rerun()
                        else:
                            error_detail = res.json().get("detail", "Error processing request")
                            st.error(f"Error ({res.status_code}): {error_detail}")
                    except Exception as e:
                        st.error(f"Failed to communicate with backend: {e}")

# --- RIGHT COLUMN: REAL-TIME AGENT ACTIVITY PANEL ---
with col_panel:
    st.subheader("🔍 Real-Time Agent Activity Panel")
    
    if st.session_state.last_activity:
        act = st.session_state.last_activity
        
        st.markdown("### 📊 Last Query Execution Metrics")
        st.info(f"**Active User Role:** {act.get('role', 'N/A')}")
        
        summary = act.get("summary", {})
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Retrieved Docs", value=summary.get("retrieved_count", 0))
        with col2:
            st.metric(label="Research Batches (RLM)", value=summary.get("research_batches_count", 0))
            
        st.markdown("---")
        st.markdown("### ⚙️ Orchestration Workflow State")
        
        # Display state transitions
        st.success("✅ **Supervisor Agent:** Analyzed Intent & Decomposed Task")
        if summary.get("research_batches_count", 0) > 0:
            st.warning("⚡ **Research Agent (RLM):** Triggered Recursive Batch Retrieval")
        elif summary.get("retrieved_count", 0) > 0:
            st.info("🔎 **Retrieval Agent:** Performed Hybrid Pinecone Search")
        st.success("📝 **Response Agent:** Verified Guardrails & Generated Output")

    else:
        st.info("Submit a chat query to inspect real-time agent workflow states, active nodes, and tool metrics.")