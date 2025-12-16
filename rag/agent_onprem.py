import json
import time
import ollama
import utils.rag_utils as utils
from rag.agent_tools import vector_tool
from rag.prompts.ticket_agent_prompt import AGENT_SYSTEM_PROMPT
from mcp.mcp_client import MCPClient

# ================================================================
# Persistent MCP client instance
# ================================================================
mcp_client = MCPClient()

# ================================================================
# LLM WRAPPER
# ================================================================
def call_llm(messages, model="llama3.1:8b-instruct-q4_K_M"):
    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]

# ================================================================
# JSON TOOL CALL PARSER
# ================================================================
def parse_tool_call(text: str):
    try:
        obj = json.loads(text)

        if isinstance(obj, dict) and "tool" in obj and "query" in obj:
            if obj["tool"] == "SQL_TOOL":
                obj["query"] = utils.to_single_line_sql(obj["query"])
            return obj
    except:
        return None
    return None

# ================================================================
# FINAL ANSWER LLM
# ================================================================
FINAL_ANSWER_PROMPT = """
You are a Telecom Remedy Analyst.

You will be given:
- The user's question
- Which tool executed
- The tool result JSON (authoritative)

Your task:
- Produce a direct, natural-language answer
- DO NOT mention SQL, JSON, tools, or backend
- DO NOT apologize
- DO NOT say “the system says”
"""

def format_final_answer(user_question, tool, result_json):
    messages = [
        {"role": "system", "content": FINAL_ANSWER_PROMPT},
        {"role": "user", "content": f"QUESTION: {user_question}\nTOOL: {tool}\nRESULT: {json.dumps(result_json)}"}
    ]
    return call_llm(messages)

# ================================================================
# MAIN AGENT PIPELINE
# ================================================================
def agent_answer(user_question: str):

    total_start = time.perf_counter()

    # ---------------- Tool Selection ----------------
    start_llm = time.perf_counter()

    LLM_AGENT_SYSTEM_PROMPT = utils.clean_system_prompt(AGENT_SYSTEM_PROMPT)

    tool_json = call_llm([
        {"role": "system", "content": LLM_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_question}
    ])
    end_llm = time.perf_counter()
    print(f"\nLLM Tool Selection Time: {end_llm - start_llm:.3f} sec")

    print("tool_json:", tool_json)
    tool_call = parse_tool_call(tool_json)

    if not tool_call:
        return f"ERROR: Invalid tool JSON returned:\n{tool_json}"

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
        start_vec = time.perf_counter()
        result = vector_tool(query)
        end_vec = time.perf_counter()
        print(f"VECTOR Search Time: {end_vec - start_vec:.3f} sec")

    else:
        return f"ERROR: Unknown tool '{tool}'"

    # ---------------- Final Answer ----------------
    start_final = time.perf_counter()
    final_answer = format_final_answer(user_question, tool, result)
    end_final = time.perf_counter()
    print(f"Final Answer Generation Time: {end_final - start_final:.3f} sec")

    total_end = time.perf_counter()
    print(f"TOTAL AGENT LATENCY: {total_end - total_start:.3f} sec")

    return final_answer

