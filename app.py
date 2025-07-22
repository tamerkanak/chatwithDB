import streamlit as st
import os
import time
from chatwithdb.metadata_extractor import extract_metadata_from_file
from chatwithdb.embedder import Embedder
from chatwithdb.qdrant_client_utils import QdrantUtils
import config
from chatwithdb.query_parser import nl_to_sql_with_metadata_gemini, summarize_sql_result_with_gemini, fix_sql_for_sqlite_with_gemini, is_valid_query_llm
import pandas as pd
import pandasql

# --- Custom Favicon and Page Config ---
favicon_url = "favicon.png"  # Use your local favicon.jpg or a public URL if needed
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

uploaded_filenames = []
if uploaded_files:
    for uploaded_file in uploaded_files:
        save_path = os.path.join(config.DATA_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        uploaded_filenames.append(uploaded_file.name)
    st.success(f"{len(uploaded_files)} file(s) uploaded: {', '.join(uploaded_filenames)}")

files = [fname for fname in os.listdir(config.DATA_DIR) if fname.endswith(".csv") or fname.endswith(".xlsx")]

if not files:
    st.warning("No CSV/XLSX files found for indexing. Please upload files.")
else:
    st.write("The following files will be indexed:")
    st.write(files)
    if st.button("Start Indexing"):
        embedder = Embedder()
        qdrant = QdrantUtils(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        qdrant.create_collection()
        progress_bar = st.progress(0)
        status_text = st.empty()
        for idx, fname in enumerate(files):
            fpath = os.path.join(config.DATA_DIR, fname)
            meta = extract_metadata_from_file(fpath)
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
            qdrant = QdrantUtils(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
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
                fpath = os.path.join(config.DATA_DIR, meta["source_file"])
                ext = os.path.splitext(fpath)[-1].lower()
                if ext == ".csv":
                    df = pd.read_csv(fpath)
                else:
                    df = pd.read_excel(fpath)
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
                    result = pandasql.sqldf(sql_for_pandasql, locals())
                    if result.empty:
                        result_str = "Result: No data found."
                    elif result.shape == (1, 1):
                        val = result.iloc[0, 0]
                        result_str = f"Result: {val}"
                    else:
                        result_str = f"Result:\n{result.to_string(index=False)}\nTotal {len(result)} row(s) returned."
                    summary = summarize_sql_result_with_gemini(query, result_str)
                    st.success(summary)
                    st.dataframe(result)
                except Exception as e:
                    st.warning("An error occurred while executing the SQL query.")
                    try:
                        fixed_sql = fix_sql_for_sqlite_with_gemini(query, sql, str(e), "df")
                        st.info("Retrying with the fixed SQL...")
                        with st.expander("Show fixed SQL command", expanded=False):
                            st.code(fixed_sql, language="sql")
                        result = pandasql.sqldf(fixed_sql, locals())
                        if result.empty:
                            result_str = "Result: No data found."
                        elif result.shape == (1, 1):
                            val = result.iloc[0, 0]
                            result_str = f"Result: {val}"
                        else:
                            result_str = f"Result:\n{result.to_string(index=False)}\nTotal {len(result)} row(s) returned."
                        summary = summarize_sql_result_with_gemini(query, result_str)
                        st.success(summary)
                        st.dataframe(result)
                    except Exception as e2:
                        st.error("The fixed SQL also failed, please enter a valid query.") 