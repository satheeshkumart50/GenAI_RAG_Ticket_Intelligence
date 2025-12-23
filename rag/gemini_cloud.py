import json
import time
import re
import os
from typing import Optional, List, Dict

import google.generativeai as genai

import utils.rag_utils as utils
from rag.agent_tools import vector_tool
from rag.prompts.ticket_agent_prompt import AGENT_SYSTEM_PROMPT
from rag.prompts.ticket_agent_prompt import FINAL_ANSWER_PROMPT_HISTORY
from mcp.mcp_client import MCPClient

# =========================
# LangChain: Chat History
# =========================
try:
    import streamlit as st  # only available in Streamlit runtime
    from langchain_community.chat_message_histories import StreamlitChatMessageHistory
    _STREAMLIT_AVAILABLE = True
except Exception:
    _STREAMLIT_AVAILABLE = False
    StreamlitChatMessageHistory = None

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage


# =====================================================================
# GOOGLE GEMINI CLIENT CONFIG
# =====================================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Activate the virtual environment before running the app."
    )
genai.configure(api_key=GOOGLE_API_KEY)

GEMINI_MODEL = "gemini-3-pro-preview"


def call_gemini(messages: list, response_mime_type="text/plain"):
    """
    Calls Gemini using a ChatML-style "messages" list.
    Handles: system/user/assistant/tool roles.
    Returns assistant text.
    """
    full_prompt = ""
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            full_prompt += f"<system>\n{content}\n</system>\n"
        elif role == "user":
            full_prompt += f"<user>\n{content}\n</user>\n"
        elif role == "assistant":
            full_prompt += f"<assistant>\n{content}\n</assistant>\n"
        elif role == "tool":
            full_prompt += f"<tool>\n{content}\n</tool>\n"

    model = genai.GenerativeModel(GEMINI_MODEL)

    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type=response_mime_type,
            temperature=0.0
        )
    )

    return response.text.strip()


# =====================================================================
# Persistent MCP Client
# =====================================================================
mcp_client = MCPClient()

# =====================================================================
# LangChain History Store (Streamlit-aware)
# =====================================================================
# Fallback store for non-Streamlit runs (tests, CLI, etc.)
_SESSION_HISTORIES: Dict[str, ChatMessageHistory] = {}


def _get_history(session_id: str, max_turns: int = 12) -> ChatMessageHistory:
    """
    Returns a LangChain chat history object.

    - In Streamlit: persists in st.session_state using StreamlitChatMessageHistory
    - Else: uses in-memory dict by session_id

    max_turns controls how many recent turns we keep (user+assistant pairs).
    """
    if _STREAMLIT_AVAILABLE and StreamlitChatMessageHistory is not None:
        hist = StreamlitChatMessageHistory(key=f"lc_history_{session_id}")
    else:
        if session_id not in _SESSION_HISTORIES:
            _SESSION_HISTORIES[session_id] = ChatMessageHistory()
        hist = _SESSION_HISTORIES[session_id]

    # Trim to last N turns to keep prompts bounded
    if max_turns is not None and max_turns > 0:
        # each "turn" ~ 2 messages (user + assistant)
        keep = max_turns * 2
        if len(hist.messages) > keep:
            hist.messages = hist.messages[-keep:]

    return hist


def _history_as_chatml(hist: ChatMessageHistory) -> List[dict]:
    """
    Convert LangChain messages -> list of {"role","content"}.
    Only keeps user/assistant roles (no tool traces).
    """
    out = []
    for m in hist.messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            out.append({"role": "assistant", "content": m.content})
    return out


# =====================================================================
# TOOL CALL PARSER (more robust)
# =====================================================================
def parse_tool_call(text: str):
    """
    Expected JSON:
    { "tool": "SQL_TOOL"|"VECTOR_TOOL", "query": "..." }
    Gemini sometimes wraps JSON with extra text, so we:
    1) try direct json.loads
    2) try extracting first {...} block
    """
    def _normalize(obj):
        if isinstance(obj, dict) and "tool" in obj and "query" in obj:
            if obj["tool"] == "SQL_TOOL":
                obj["query"] = utils.to_single_line_sql(obj["query"])
            return obj
        return None

    # 1) direct parse
    try:
        obj = json.loads(text)
        norm = _normalize(obj)
        if norm:
            return norm
    except Exception:
        pass

    # 2) extract first JSON object block
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            obj = json.loads(match.group(0))
            norm = _normalize(obj)
            if norm:
                return norm
    except Exception:
        pass

    return None


# =====================================================================
# NATURAL LANGUAGE FINAL ANSWER FORMATTER
# =====================================================================
def format_final_answer(user_question, tool, result_json, chat_context: Optional[str] = None):
    context_block = f"\nCHAT_CONTEXT:\n{chat_context}\n" if chat_context else ""
    messages = [
        {"role": "system", "content": FINAL_ANSWER_PROMPT_HISTORY},
        {"role": "user", "content": (
            f"QUESTION: {user_question}\n"
            f"TOOL: {tool}\n"
            f"RESULT: {json.dumps(result_json)}"
            f"{context_block}"
        )}
    ]
    return call_gemini(messages)


# =====================================================================
# MAIN AGENT PIPELINE (NOW HISTORY-AWARE VIA LANGCHAIN)
# =====================================================================
def agent_answer(user_question: str, session_id: str = "default", max_history_turns: int = 12):
    """
    History-aware Gemini agent using LangChain chat memory.

    - Keeps prior user/assistant turns in LangChain memory.
    - Feeds recent history into tool-selection prompt (so follow-ups work).
    - Stores ONLY clean final answers (no SQL/JSON) in memory.
    """
    total_start = time.perf_counter()

    # -------- Load / get history --------
    hist = _get_history(session_id=session_id, max_turns=max_history_turns)

    # Add current user message to history FIRST
    hist.add_message(HumanMessage(content=user_question))

    # Convert recent history to ChatML-like list
    recent_chatml = _history_as_chatml(hist)

    # ---------------- clean system prompts ----------------
    sys_prompt = utils.clean_system_prompt(AGENT_SYSTEM_PROMPT)

    # Tool selection sees:
    # system + recent chat (user/assistant) which includes current user question
    tool_json_raw = call_gemini(
        [{"role": "system", "content": sys_prompt}] + recent_chatml,
        response_mime_type="application/json"
    )

    tool_call = parse_tool_call(tool_json_raw)

    if not tool_call:
        # store safe error response (optional)
        err_msg = f"ERROR: Invalid tool JSON returned:\n{tool_json_raw}"
        hist.add_message(AIMessage(content="I couldn’t interpret the tool selection output. Please rephrase the question."))
        return err_msg

    tool = tool_call["tool"]
    query = tool_call["query"]

    # ---------------- Tool Execution ----------------
    if tool == "SQL_TOOL":
        print("RAW SQL:", query)
        start_sql = time.perf_counter()

        result = mcp_client.sql_query(query)

        end_sql = time.perf_counter()
        print(f"SQL Execution Time: {end_sql - start_sql:.3f} sec")
        print("SQL MCP RAW RESULT:", result)

        if isinstance(result, dict) and "error" in result:
            safe_err = "I hit an issue retrieving the data for that request. Try narrowing the filter or date range."
            hist.add_message(AIMessage(content=safe_err))
            return f"SQL ERROR: {result['error']}"

    elif tool == "VECTOR_TOOL":
        result = vector_tool(query)

    else:
        safe_err = "I couldn't route that request to a supported tool."
        hist.add_message(AIMessage(content=safe_err))
        return f"ERROR: Unknown tool '{tool}'"

    # ---------------- Final Answer Generation ----------------
    # Provide lightweight chat context to help resolve pronouns like "that region"
    # (kept small so it doesn't blow up the prompt)
    chat_context = None
    try:
        # last 6 messages worth of context
        ctx_msgs = recent_chatml[-6:]
        chat_context = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in ctx_msgs])
    except Exception:
        chat_context = None

    final_answer = format_final_answer(user_question, tool, result, chat_context=chat_context)

    # Store ONLY the clean final answer (no SQL/JSON/tool traces) in history
    hist.add_message(AIMessage(content=final_answer))

    total_end = time.perf_counter()
    print(f"TOTAL LATENCY: {total_end - total_start:.3f} sec")

    return final_answer
