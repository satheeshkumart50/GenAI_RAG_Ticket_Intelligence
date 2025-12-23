import streamlit as st
from rag.agent_onprem import agent_answer as onpremllm
from rag.gemini_nochain import agent_answer as cloudllm

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

# Force white theme (Streamlit 1.28+)
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
            max-height: calc(100vh - 320px);  /* a bit smaller to leave room */
            overflow-y: auto;
            padding-right: 1rem;
            padding-bottom: 140px;  /* <-- buffer above the fixed FAQ bar */
        }

        /* FAQ BAR: fixed above chat_input, narrower & centered */
        div[data-testid="stSelectbox"] {
            position: fixed;
            bottom: 80px;              /* space above chat input */
            left: 50%;
            transform: translateX(-50%);
            width: 70%;                 /* reduced width */
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
            position: relative;              /* anchor for ::before */
            background-color: #ffffff;
        }

        header[data-testid="stHeader"]::before {
            content: "Incident Decision Support";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 1rem;
            font-weight: 600;
            color: #262730;
            pointer-events: none;            /* don't block clicks on Deploy menu */
        }

        /* Extra bottom padding for the whole main area, for FAQ + chat_input */
        div[data-testid="stChatInput"] {
            margin-bottom: 24px;   /* adjust 24 → 40 if you want it higher */
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
    "When the CR for this ticket INC0001 start and end?",
    "provide a breakdown of tickets created every month",
    ]

# Initialize session_state keys
if "messages" not in st.session_state:
    st.session_state.messages = []

if "faq_prev" not in st.session_state:
    st.session_state.faq_prev = FAQ_DEFAULT

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

# ---------------------------------------------------------
# Chat Message Container (history)
# ---------------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar=USER_AVATAR).markdown(msg["content"])
    else:
        st.chat_message("assistant", avatar=BOT_AVATAR).markdown(msg["content"])

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
        # This sets session_state, but note: st.chat_input
        # cannot be pre-filled visually; user still sees an empty bar.
        st.session_state.user_question = faq_choice

# ---------------------------------------------------------
# Chat Input (pinned at very bottom by Streamlit)
# ---------------------------------------------------------
user_input = st.chat_input(
    "Ask anything about tickets, CR windows, outages...",
    key="user_question"  # bound to st.session_state.user_question
)

if user_input:
    # Display user message
    st.chat_message("user", avatar=USER_AVATAR).markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Call backend LLM
    with st.spinner("..."):
        response = cloudllm(user_input)

    # Display assistant message
    st.chat_message("assistant", avatar=BOT_AVATAR).markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
