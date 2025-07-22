import google.generativeai as genai
import config
import re

def nl_to_sql_with_metadata_gemini(nl_query: str, table_name: str, columns: list, column_types: list) -> str:
    """
    Converts a natural language query to SQL using Gemini, with table metadata.
    """
    genai.configure(api_key=config.GEMINI_API_KEY)
    prompt = f"""
Table name: {table_name}
Columns:
{chr(10).join([f"- {col}: {typ}" for col, typ in zip(columns, column_types)])}
User query: {nl_query}
Generate a single SQL command using only this table, only SELECT statements, and do not modify data. Do NOT use multiple SQL commands, UNION, or UNION ALL. Add WHERE, ORDER BY, LIMIT if needed. Return only a single SQL code.
"""
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    sql = response.text.strip()
    # Remove code block markers
    sql = re.sub(r"^```sql\s*|^```|```$", "", sql, flags=re.MULTILINE).strip()
    return sql

def summarize_sql_result_with_gemini(nl_query: str, sql_result: str) -> str:
    """
    Summarizes the SQL query result for the user in a formal and conversational style using Gemini.
    """
    import google.generativeai as genai
    import config
    genai.configure(api_key=config.GEMINI_API_KEY)
    prompt = f"""
You are a database assistant. The user's natural language query and the SQL query result are given below.
Provide a clear, concise, and user-friendly summary in a formal and conversational style. Summarize the result as a table if needed, or explain numerically if appropriate. Avoid unnecessary technical details.

User query:
{nl_query}

SQL result:
{sql_result}

Your answer:
"""
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    return response.text.strip()

def fix_sql_for_sqlite_with_gemini(nl_query: str, sql: str, error_msg: str, table_name: str) -> str:
    import google.generativeai as genai
    import config
    genai.configure(api_key=config.GEMINI_API_KEY)
    prompt = f"""
User's natural language query:
{nl_query}

Generated SQL:
{sql}

Received error:
{error_msg}

Please fix the above SQL to be compatible with SQLite. Return only the SQL code. Use '{table_name}' as the table name.
"""
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    sql_fixed = response.text.strip()
    # Remove code block markers
    import re
    sql_fixed = re.sub(r"^```sql\s*|^```|```$", "", sql_fixed, flags=re.MULTILINE).strip()
    return sql_fixed 

def is_valid_query_llm(nl_query: str) -> bool:
    """
    Checks with Gemini if the given query is a meaningful natural language query for a database assistant.
    """
    import google.generativeai as genai
    import config
    genai.configure(api_key=config.GEMINI_API_KEY)
    prompt = f"""
Is the following text a meaningful natural language query addressed to a database assistant?
Answer only 'yes' or 'no'.

Query:
{nl_query}
"""
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content(prompt)
    yanit = response.text.strip().lower()
    return yanit.startswith('yes') 