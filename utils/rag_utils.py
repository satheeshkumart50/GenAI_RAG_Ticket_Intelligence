import re

def clean_system_prompt(prompt: str) -> str:
    """
    Removes unnecessary visual separators from the system prompt
    to optimize clarity and reduce token usage before sending
    to the LLM.
    """

    # 1. Remove ASCII separators like ========, ---------, ********
    prompt = re.sub(r"[=\-*]{5,}", "", prompt)

    # 2. Remove repeating blank lines
    prompt = re.sub(r"\n\s*\n+", "\n", prompt)

    # 3. Trim spaces around lines
    cleaned_lines = [line.rstrip() for line in prompt.split("\n")]
    prompt = "\n".join(cleaned_lines)

    # 4. Extra safety: collapse multiple spaces
    prompt = re.sub(r"[ ]{2,}", " ", prompt)

    # 5. Strip overall prompt
    return prompt.strip()



# ================================================================
# 7. STRIP NEW LINES FROM SQL
# ================================================================
def to_single_line_sql(sql_text: str) -> str:
    """
    Convert multi-line SQL into a safe single-line SQL statement.
    Steps:
    - Remove newlines and excessive whitespace
    - Collapse multiple spaces into a single space
    - Preserve spacing around SQL keywords, operators, and punctuation
    """
    if not sql_text:
        return ""

    # Remove newlines and tabs
    sql = sql_text.replace("\n", " ").replace("\r", " ").replace("\t", " ")

    # Collapse multiple spaces into single spaces
    sql = re.sub(r"\s+", " ", sql)

    # Trim spaces before semicolon and normalize ending
    sql = sql.strip()
    
    # Ensure only ONE semicolon at the end
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    return sql + ";"