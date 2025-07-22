import streamlit as st
import os
import time
import io
import pandas as pd
import pandasql
from chatwithdb.metadata_extractor import extract_metadata_from_file
from chatwithdb.embedder import Embedder
from chatwithdb.qdrant_client_utils import QdrantUtils
import config
from chatwithdb.query_parser import (
    nl_to_sql_with_metadata_gemini,
    summarize_sql_result_with_gemini,
    fix_sql_for_sqlite_with_gemini,
    is_valid_query_llm
)

# --- Custom Favicon and Page Config ---
favicon_url = "favicon.png"
st.set_page_config(
    page_title="ChatWithDB",
    page_icon=favicon_url,
    layout="wide"
)

# --- Sidebar: Developer Info ---
st.sidebar.markdown("""
<div style="margin-bottom: 1.2em;">
  <span style="font-size:1.1em; font-weight:700; color:#235390;">Developed by Tamer Kanak</span><br>
  <a href="https://github.com/tamerkanak" target="_blank" style="display:inline-block; margin: 0.3em 0; font-size:1.08em; font-weight:600; color:#222; text-decoration:none;">GitHub ↗</a><br>
  <a href="https://www.linkedin.com/in/tamerkanak/" target="_blank" style="display:inline-block; margin: 0.1em 0; font-size:1.08em; font-weight:600; color:#0a66c2; text-decoration:none;">LinkedIn ↗</a>
</div>
---

**How to use:**
1. Upload your CSV/XLSX files
2. Click 'Start Indexing'
3. Ask questions about your data

ChatWithDB lets you chat with your own tables!
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# --- Header Section ---
st.markdown(
    """
    <div style='background: linear-gradient(90deg, #4f8bf9 0%, #235390 100%); padding: 1.2rem 2rem; border-radius: 18px; box-shadow: 0 4px 24px #0002; display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 1.2rem; text-align: center;'>
        <div style='color: #fff;'>
            <h1 style='margin-bottom: 0.2rem; font-size: 2.5rem; font-weight: 800; letter-spacing: 1px;'>ChatWithDB</h1>
            <span style='font-size:1.25rem; color: #e0e6f7;'>Chat with Your CSV Tables in Style 🚀</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# --- File Upload and Indexing ---
st.header("1. Index Tables")

uploaded_files = st.file_uploader(
    "Select and upload CSV/XLSX files from your computer:",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

# Her kullanıcıya özel dosya saklama
if "user_files" not in st.session_state:
    st.session_state["user_files"] = {}

uploaded_filenames = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        st.session_state["user_files"][uploaded_file.name] = uploaded_file.getvalue()
        uploaded_filenames.append(uploaded_file.name)
    st.success(f"{len(uploaded_files)} file(s) uploaded: {', '.join(uploaded_filenames)}")

files = list(st.session_state["user_files"].keys())

if not files:
    st.warning("No CSV/XLSX files found for indexing. Please upload files.")
else:
    st.write("The following files will be indexed:")
    st.write(files)
    if st.button("Start Indexing"):
        embedder = Embedder()
        qdrant = QdrantUtils(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        qdrant.create_collection()
        progress_bar = st.progress(0)
        status_text = st.empty()
        for idx, fname in enumerate(files):
            file_bytes = st.session_state["user_files"][fname]
            ext = os.path.splitext(fname)[-1].lower()
            # Dosyayı DataFrame olarak oku
            if ext == ".csv":
                df = pd.read_csv(io.BytesIO(file_bytes), nrows=100)
            else:
                df = pd.read_excel(io.BytesIO(file_bytes), nrows=100)
            # Metadata çıkarımı
            table_name = os.path.splitext(fname)[0]
            columns = list(df.columns)
            column_types = []
            for col in columns:
                dtype = df[col]
                if pd.api.types.is_numeric_dtype(dtype):
                    column_types.append("numeric")
                elif pd.api.types.is_string_dtype(dtype):
                    column_types.append("string")
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    column_types.append("datetime")
                elif pd.api.types.is_bool_dtype(dtype):
                    column_types.append("boolean")
                else:
                    column_types.append("unknown")
            metadata_text = f"Table: {table_name}\nColumns:\n" + "\n".join([
                f"- {col}: {typ}" for col, typ in zip(columns, column_types)
            ])
            meta = {
                "table_name": table_name,
                "columns": columns,
                "column_types": column_types,
                "metadata_text": metadata_text,
                "source_file": fname
            }
            embedding = embedder.embed_metadata(meta["metadata_text"])
            qdrant.upload_metadata(embedding, {
                "table_name": meta["table_name"],
                "columns": meta["columns"],
                "column_types": meta["column_types"],
                "source_file": meta["source_file"]
            }, point_id=idx)
            percent = int((idx+1)/len(files)*100)
            progress_bar.progress((idx+1)/len(files))
            status_text.info(f"{fname} indexed. ({percent}%)")
            time.sleep(0.2)
        status_text.success("All files have been successfully indexed!")

st.markdown("---")

# --- Natural Language Query ---
st.header("2. Natural Language Query")
query = st.text_input("Ask a question about your tables:")

if st.button("Query") and query:
    if not is_valid_query_llm(query):
        st.error("Please enter a meaningful natural language query.")
    else:
        with st.spinner("Assistant is thinking..."):
            embedder = Embedder()
            qdrant = QdrantUtils(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
            embedding = embedder.embed_query(query)
            hits = qdrant.search(embedding, top_k=1)
            if not hits:
                st.warning("No matching table found.")
            else:
                meta = hits[0].payload
                score = getattr(hits[0], 'score', None)
                if score is not None:
                    percent = int(score * 100)
                    st.info(f"With a {percent}% match, the relevant data is likely in the {meta['table_name']} ({meta['source_file']}) table.")
                else:
                    st.info(f"Best matching table: {meta['table_name']} ({meta['source_file']})")
                # Dosyayı session_state'den oku
                file_bytes = st.session_state["user_files"].get(meta["source_file"])
                if not file_bytes:
                    st.error("File not found in your session. Please re-upload.")
                else:
                    ext = os.path.splitext(meta["source_file"])[-1].lower()
                    if ext == ".csv":
                        df = pd.read_csv(io.BytesIO(file_bytes))
                    else:
                        df = pd.read_excel(io.BytesIO(file_bytes))
                    sql = nl_to_sql_with_metadata_gemini(
                        query,
                        meta["table_name"],
                        meta["columns"],
                        meta["column_types"]
                    )
                    with st.expander("Show SQL command", expanded=False):
                        st.code(sql, language="sql")
                    try:
                        sql_for_pandasql = sql.replace(meta["table_name"], "df")
                        result = pandasql.sqldf(sql_for_pandasql, {"df": df})
                        if result.empty:
                            result_str = "Result: No data found."
                        elif result.shape == (1, 1):
                            val = result.iloc[0, 0]
                            result_str = f"Result: {val}"
                        else:
                            result_str = f"Result:\n{result.to_string(index=False)}\nTotal {len(result)} row(s) returned."
                        summary = summarize_sql_result_with_gemini(query, result_str)
                        st.markdown("**Assistant:**")
                        st.write(summary)
                    except Exception as e:
                        st.error(f"An error occurred while executing the SQL query: {e}")
                        # Try to fix with Gemini
                        try:
                            fixed_sql = fix_sql_for_sqlite_with_gemini(query, sql, str(e), "df")
                            st.info("Retrying with the fixed SQL:")
                            st.code(fixed_sql, language="sql")
                            result = pandasql.sqldf(fixed_sql, {"df": df})
                            if result.empty:
                                result_str = "Result: No data found."
                            elif result.shape == (1, 1):
                                val = result.iloc[0, 0]
                                result_str = f"Result: {val}"
                            else:
                                result_str = f"Result:\n{result.to_string(index=False)}\nTotal {len(result)} row(s) returned."
                            summary = summarize_sql_result_with_gemini(query, result_str)
                            st.markdown("**Assistant:**")
                            st.write(summary)
                        except Exception as e2:
                            st.error(f"The fixed SQL also failed: {e2}") 
