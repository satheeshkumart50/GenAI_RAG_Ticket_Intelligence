import uuid
import streamlit as st

from rag.agent_onprem import agent_answer as onpremllm
from rag.gemini_nochain import agent_answer as cloudllm
from rag.gemini_cloud import agent_answer as gemini
from rag.openai_cloud import agent_answer as openai

from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# ---------------------------------------------------------
# AVATARS
# ---------------------------------------------------------
USER_AVATAR = "🧑‍💻"
BOT_AVATAR = "✨"

# ---------------------------------------------------------
# Streamlit Page Settings
# ---------------------------------------------------------
st.set_page_config(
    page_title="Incident Decision Support",
    #page_icon="📡",
    layout="wide"
)

# ---------------------------------------------------------
# Create a stable session_id for LangChain memory
# ---------------------------------------------------------
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())

SESSION_ID = st.session_state.chat_session_id

# This is the SAME key used inside agent_cloud.py:
# StreamlitChatMessageHistory(key=f"lc_history_{session_id}")
lc_history = StreamlitChatMessageHistory(key=f"lc_history_{SESSION_ID}")

# ---------------------------------------------------------
# Force white theme (Streamlit 1.28+)
# ---------------------------------------------------------
st.markdown("""
    <style>
        :root {
            --background-color: #ffffff !important;
            --text-color: #000000 !important;
        }

        /* Optional: make bot avatar round */
        img[alt="assistant avatar"] {
            border-radius: 50% !important;
        }
        img[alt="user avatar"] {
            border-radius: 50% !important;
        }

        /* CHAT AREA: scrollable, with bottom padding so it doesn't hide under FAQ */
        div[data-testid="stVerticalBlock"]:has(div[data-testid="stChatMessage"]) {
            max-height: calc(100vh - 320px);
            overflow-y: auto;
            padding-right: 1rem;
            padding-bottom: 140px;
        }

        /* FAQ BAR: fixed above chat_input, narrower & centered */
        div[data-testid="stSelectbox"] {
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            width: 70%;
            max-width: 960px;
            padding: 0.75rem 1rem 1rem;
            background-color: #ffffff;
            z-index: 999;
            border-top: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
            box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.03);
        }

        /* ===== Small title in the top header bar ===== */
        header[data-testid="stHeader"] {
            position: relative;
            background-color: #ffffff;
        }

        header[data-testid="stHeader"]::before {
            content: "Incident Decision Support - GPT-5.0";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 2rem;
            font-weight: 600;
            color: #262730;
            pointer-events: none;
        }

        /* Extra bottom padding for the whole main area, for FAQ + chat_input */
        div[data-testid="stChatInput"] {
            margin-bottom: 24px;
        }
            
        /* Disable typing in FAQ dropdown */   
        div[data-testid="stSelectbox"] input {
            pointer-events: none;      /* disables typing */
            caret-color: transparent;  /* hides cursor */
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FAQ DROPDOWN SETUP
# ---------------------------------------------------------
FAQ_DEFAULT = "Select a question..."
FAQ_QUESTIONS = [
    "Can you provide an analysis on the number of hubs in any west region that are currently being on the node NODE-101?",
    "Can you provide an analysis of the number of incidents for Dallas that have been closed with the Agent AutoMonitorX or NoiseReducer in the last month?",
    "How many times has hub HUB-D4 been affected this month?",
    "What INC or CRQ is related to INC0325?",
    "When the CR for this ticket INC0002 start and end?",
    "what is the root cause of impact on INC0001?",
    "What was last INC on the node NODE-505?",
    "provide a graphical view on number of tickets created every month",
    "Provide breakdown on the number of cancelled tickets per node per month",

    # "Summarize INC0002.",
    # "What are the key worklog actions taken?",
    # "When did the CR start and end for this ticket (UTC)?",
    # "Is the ticket created before or after CR start, and by how long?",
    # "How many tickets were created before CR start time in the last 6 months?",
    # "provide a graphical view on those tickets per month",
    # "For those tickets, which city appears most?",
    # "In that city, list the top 10 agents.",
    # "For the top agent, summarize 2 recent tickets.",
]

# Initialize session_state keys for FAQ + chat_input binding
if "faq_prev" not in st.session_state:
    st.session_state.faq_prev = FAQ_DEFAULT

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

# ---------------------------------------------------------
# Chat Message Container (render from LangChain history)
# ---------------------------------------------------------
for m in lc_history.messages:
    if isinstance(m, HumanMessage):
        st.chat_message("user", avatar=USER_AVATAR).markdown(m.content)
    elif isinstance(m, AIMessage):
        st.chat_message("assistant", avatar=BOT_AVATAR).markdown(m.content)

# ---------------------------------------------------------
# FAQ DROPDOWN (VISUALLY FIXED ABOVE CHAT INPUT)
# ---------------------------------------------------------
faq_choice = st.selectbox(
    "FAQ",
    [FAQ_DEFAULT] + FAQ_QUESTIONS,
    key="faq_choice"
)

# If the FAQ selection changes, copy it into the chat input once
if faq_choice != st.session_state.faq_prev:
    st.session_state.faq_prev = faq_choice
    if faq_choice != FAQ_DEFAULT:
        # This updates the bound state for chat_input
        st.session_state.user_question = faq_choice

# ---------------------------------------------------------
# Chat Input (pinned at very bottom by Streamlit)
# ---------------------------------------------------------
user_input = st.chat_input(
    "Ask anything about tickets, CR windows, outages...",
    key="user_question"
)

if user_input:
    # Display user message immediately (agent will also store it in LangChain history)
    st.chat_message("user", avatar=USER_AVATAR).markdown(user_input)

    # Call backend LLM (history-aware via session_id)
    with st.spinner("..."):
        # Choose which backend you want (cloud or onprem)
        # response = onpremllm(user_input, session_id=SESSION_ID, max_history_turns=12)
        response = openai(user_input, session_id=SESSION_ID, max_history_turns=12)

    # Display assistant message immediately (agent will also store it in LangChain history)
    st.chat_message("assistant", avatar=BOT_AVATAR).markdown(response)
