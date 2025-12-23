import json
import time
import re
import os
from typing import Optional, List, Dict

from openai import OpenAI

import utils.rag_utils as utils
from rag.agent_tools import vector_tool
from rag.prompts.ticket_agent_prompt import AGENT_SYSTEM_PROMPT
from rag.prompts.ticket_agent_prompt import FINAL_ANSWER_PROMPT_HISTORY
from mcp.mcp_client import MCPClient

# =========================
# LangChain: Chat History
# =========================
try:
    import streamlit as st
    from langchain_community.chat_message_histories import StreamlitChatMessageHistory
    _STREAMLIT_AVAILABLE = True
except Exception:
    _STREAMLIT_AVAILABLE = False
    StreamlitChatMessageHistory = None

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage


# =====================================================================
# OPENAI CLIENT CONFIG (GPT-5.2)
# =====================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

GPT_MODEL = "gpt-5.2"


# =====================================================================
# LLM CALL WRAPPER
# =====================================================================
def call_openai(messages: list, response_format: Optional[dict] = None):
    """
    Calls OpenAI GPT-5.2 using Chat Completions.
    Supports strict JSON output for tool selection.
    """
    kwargs = {
        "model": GPT_MODEL,
        "messages": messages,
        "temperature": 0.0,
    }

    if response_format:
        kwargs["response_format"] = response_format

    response = client.chat.completions.create(**kwargs)

    return response.choices[0].message.content.strip()


# =====================================================================
# Persistent MCP Client
# =====================================================================
mcp_client = MCPClient()


# =====================================================================
# LangChain History Store
# =====================================================================
_SESSION_HISTORIES: Dict[str, ChatMessageHistory] = {}

def _get_history(session_id: str, max_turns: int = 12) -> ChatMessageHistory:
    if _STREAMLIT_AVAILABLE and StreamlitChatMessageHistory is not None:
        hist = StreamlitChatMessageHistory(key=f"lc_history_{session_id}")
    else:
        if session_id not in _SESSION_HISTORIES:
            _SESSION_HISTORIES[session_id] = ChatMessageHistory()
        hist = _SESSION_HISTORIES[session_id]

    if max_turns:
        keep = max_turns * 2
        if len(hist.messages) > keep:
            hist.messages = hist.messages[-keep:]

    return hist


def _history_as_chatml(hist: ChatMessageHistory) -> List[dict]:
    out = []
    for m in hist.messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            out.append({"role": "assistant", "content": m.content})
    return out


# =====================================================================
# TOOL CALL PARSER
# =====================================================================
def parse_tool_call(text: str):
    def _normalize(obj):
        if isinstance(obj, dict) and "tool" in obj and "query" in obj:
            if obj["tool"] == "SQL_TOOL":
                obj["query"] = utils.to_single_line_sql(obj["query"])
            return obj
        return None

    try:
        obj = json.loads(text)
        norm = _normalize(obj)
        if norm:
            return norm
    except Exception:
        pass

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
# FINAL ANSWER FORMATTER
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

    return call_openai(messages)


# =====================================================================
# MAIN AGENT PIPELINE (GPT-5.2)
# =====================================================================
def agent_answer(user_question: str, session_id: str = "default", max_history_turns: int = 12):

    total_start = time.perf_counter()

    hist = _get_history(session_id=session_id, max_turns=max_history_turns)
    hist.add_message(HumanMessage(content=user_question))

    recent_chatml = _history_as_chatml(hist)

    sys_prompt = utils.clean_system_prompt(AGENT_SYSTEM_PROMPT)

    # ---------- Tool Selection ----------
    tool_json_raw = call_openai(
        [{"role": "system", "content": sys_prompt}] + recent_chatml,
        response_format={"type": "json_object"}
    )

    tool_call = parse_tool_call(tool_json_raw)

    if not tool_call:
        hist.add_message(AIMessage(
            content="I couldn’t interpret the request. Please rephrase."
        ))
        return f"ERROR: Invalid tool JSON returned:\n{tool_json_raw}"

    tool = tool_call["tool"]
    query = tool_call["query"]

    # ---------- Tool Execution ----------
    if tool == "SQL_TOOL":
        print("RAW SQL:", query)
        start_sql = time.perf_counter()

        result = mcp_client.sql_query(query)

        end_sql = time.perf_counter()
        print(f"SQL Execution Time: {end_sql - start_sql:.3f} sec")
        print("SQL MCP RAW RESULT:", result)

        if isinstance(result, dict) and "error" in result:
            safe_err = "I encountered an issue retrieving that data."
            hist.add_message(AIMessage(content=safe_err))
            return safe_err

    elif tool == "VECTOR_TOOL":
        print("RAW Vector SQL:", query)
        start_sql = time.perf_counter()

        result = vector_tool(query)

        end_sql = time.perf_counter()
        print(f"Vector SQL Execution Time: {end_sql - start_sql:.3f} sec")
        print("VectorSQL MCP RAW RESULT:", result)

    else:
        safe_err = "Unsupported tool selection."
        hist.add_message(AIMessage(content=safe_err))
        return safe_err

    # ---------- Final Answer ----------
    chat_context = None
    try:
        ctx_msgs = recent_chatml[-6:]
        chat_context = "\n".join(
            [f"{m['role'].upper()}: {m['content']}" for m in ctx_msgs]
        )
    except Exception:
        pass

    final_answer = format_final_answer(
        user_question, tool, result, chat_context=chat_context
    )

    hist.add_message(AIMessage(content=final_answer))

    total_end = time.perf_counter()
    print(f"TOTAL LATENCY: {total_end - total_start:.3f} sec")

    return final_answer
