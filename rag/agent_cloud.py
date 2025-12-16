import json
import time
import os
import google.generativeai as genai
import utils.rag_utils as utils
from rag.agent_tools import vector_tool
from rag.prompts.ticket_agent_prompt import AGENT_SYSTEM_PROMPT
from rag.prompts.ticket_agent_prompt import FINAL_ANSWER_PROMPT
from mcp.mcp_client import MCPClient


# =====================================================================
# GOOGLE GEMINI CLIENT CONFIG
# =====================================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Activate the virtual environment before running the app."
    )
genai.configure(api_key=GOOGLE_API_KEY)

GEMINI_MODEL = "gemini-3-pro-preview"         # Flash 2.5 model


def call_gemini(messages: list, response_mime_type="text/plain"):
    """
    Calls Gemini 2.0 Flash model using a ChatML-style "messages" list.
    Handles only 'system' and 'user' roles.
    Assistant messages are returned as plain text.
    """
    # Convert OpenAI-style list → Gemini-style prompt string
    full_prompt = ""
    for msg in messages:
        if msg["role"] == "system":
            full_prompt += f"<system>\n{msg['content']}\n</system>\n"
        elif msg["role"] == "user":
            full_prompt += f"<user>\n{msg['content']}\n</user>\n"
        elif msg["role"] == "assistant":
            full_prompt += f"<assistant>\n{msg['content']}\n</assistant>\n"
        elif msg["role"] == "tool":
            full_prompt += f"<tool>\n{msg['content']}\n</tool>\n"

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
# TOOL CALL PARSER
# =====================================================================
def parse_tool_call(text: str):
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "tool" in obj and "query" in obj:
            # Clean SQL
            if obj["tool"] == "SQL_TOOL":
                obj["query"] = utils.to_single_line_sql(obj["query"])
            return obj
    except:
        return None
    return None


# =====================================================================
# NATURAL LANGUAGE FINAL ANSWER
# =====================================================================
def format_final_answer(user_question, tool, result_json):
    messages = [
        {"role": "system", "content": FINAL_ANSWER_PROMPT},
        {"role": "user", "content": f"QUESTION: {user_question}\nTOOL: {tool}\nRESULT: {json.dumps(result_json)}"}
    ]
    return call_gemini(messages)


# =====================================================================
# MAIN AGENT PIPELINE
# =====================================================================
def agent_answer(user_question: str):
    total_start = time.perf_counter()

    # ---------------- Tool Selection ----------------
    sys_prompt = utils.clean_system_prompt(AGENT_SYSTEM_PROMPT)

    tool_json_raw = call_gemini([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_question}
    ], response_mime_type="application/json")

    tool_call = parse_tool_call(tool_json_raw)

    if not tool_call:
        return f"ERROR: Invalid tool JSON returned:\n{tool_json_raw}"

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

        if "error" in result:
            return f"SQL ERROR: {result['error']}"

    elif tool == "VECTOR_TOOL":
        result = vector_tool(query)

    else:
        return f"ERROR: Unknown tool '{tool}'"

    # ---------------- Final Answer Generation ----------------
    final_answer = format_final_answer(user_question, tool, result)

    total_end = time.perf_counter()
    print(f"TOTAL LATENCY: {total_end - total_start:.3f} sec")

    return final_answer
