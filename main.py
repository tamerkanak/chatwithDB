import os
from chatwithdb.metadata_extractor import extract_metadata_from_file
from chatwithdb.embedder import Embedder
from chatwithdb.qdrant_client_utils import QdrantUtils
import config
import pandas as pd
import pandasql
from chatwithdb.query_parser import nl_to_sql_with_metadata_gemini, summarize_sql_result_with_gemini, fix_sql_for_sqlite_with_gemini, is_valid_query_llm

def index_all_files():
    embedder = Embedder()
    qdrant = QdrantUtils(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    qdrant.create_collection()
    files = [fname for fname in os.listdir(config.DATA_DIR) if fname.endswith(".csv") or fname.endswith(".xlsx")]
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
        print(f"Indexed: {fname}")

def search_table(nl_query: str):
    embedder = Embedder()
    qdrant = QdrantUtils(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    embedding = embedder.embed_query(nl_query)
    hits = qdrant.search(embedding, top_k=1)
    if not hits:
        print("No matching table found.")
        return None
    hit = hits[0]
    meta = hit.payload
    score = hit.score if hasattr(hit, 'score') else None
    print(f"Best match: {meta['table_name']} ({meta['source_file']})")
    if score is not None:
        print(f"Similarity score (confidence): {score:.3f}")
    return meta

def run_readonly_query(meta, nl_query):
    fpath = os.path.join(config.DATA_DIR, meta["source_file"])
    ext = os.path.splitext(fpath)[-1].lower()
    if ext == ".csv":
        df = pd.read_csv(fpath)
    else:
        df = pd.read_excel(fpath)
    # Generate SQL with Gemini
    sql = nl_to_sql_with_metadata_gemini(
        nl_query,
        meta["table_name"],
        meta["columns"],
        meta["column_types"]
    )
    print(f"Generated SQL:\n{sql}")
    try:
        sql_for_pandasql = sql.replace(meta["table_name"], "df")
        result = pandasql.sqldf(sql_for_pandasql, locals())
        # Prepare result as string
        if result.empty:
            result_str = "Result: No data found."
        elif result.shape == (1, 1):
            val = result.iloc[0, 0]
            result_str = f"Result: {val}"
        else:
            result_str = f"Result:\n{result.to_string(index=False)}\nTotal {len(result)} row(s) returned."
        # Summarize with LLM
        summary = summarize_sql_result_with_gemini(nl_query, result_str)
        print("Assistant:")
        print(summary)
    except Exception as e:
        print("An error occurred while executing the SQL query:", e)
        # Try to fix with Gemini
        try:
            fixed_sql = fix_sql_for_sqlite_with_gemini(nl_query, sql, str(e), "df")
            print("Retrying with the fixed SQL:")
            print(fixed_sql)
            result = pandasql.sqldf(fixed_sql, locals())
            if result.empty:
                result_str = "Result: No data found."
            elif result.shape == (1, 1):
                val = result.iloc[0, 0]
                result_str = f"Result: {val}"
            else:
                result_str = f"Result:\n{result.to_string(index=False)}\nTotal {len(result)} row(s) returned."
            summary = summarize_sql_result_with_gemini(nl_query, result_str)
            print("Assistant:")
            print(summary)
        except Exception as e2:
            print("The fixed SQL also failed:", e2)

def main():
    print("1. Index files\n2. Query")
    choice = input("Choice: ")
    if choice == "1":
        index_all_files()
    elif choice == "2":
        while True:
            nl_query = input("Enter your query (type 'q' to quit): ")
            if nl_query.strip().lower() == 'q':
                print("Exiting...")
                break
            if not is_valid_query_llm(nl_query):
                print("Please enter a meaningful natural language query.")
                continue
            meta = search_table(nl_query)
            if meta:
                run_readonly_query(meta, nl_query)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main() 