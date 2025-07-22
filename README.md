# ChatWithDB

ChatWithDB lets you chat with your own CSV or Excel database tables using natural language! You can upload, index, and query your data interactively, powered by LLMs and vector search.

---

## Features

- **Upload and Index**: Upload your CSV/XLSX files and index them for semantic search.
- **Natural Language Query**: Ask questions about your data in plain English; get SQL queries and summarized results.
- **Progress Tracking**: See progress bars and status messages during indexing.
- **Secure API Key Handling**: Your API key is stored securely in a `.env` file.

---

## How It Works

1. **File Upload & Indexing**:  
   - Upload your CSV/XLSX files via the web interface.
   - The app extracts metadata (table name, columns, types) and generates vector embeddings using a SentenceTransformer model.
   - Metadata embeddings are stored in a Qdrant vector database for fast semantic search.

2. **Querying**:  
   - Enter a natural language question about your data.
   - The app finds the most relevant table using vector similarity.
   - It uses Google Gemini LLM to convert your question and table metadata into an SQL query.
   - The SQL is executed on your data, and the results are summarized using the LLM.

---

## Project Structure

```
ChatWithDB/
│
├── app.py                # Main Streamlit web app
├── main.py               # CLI entry point (optional)
├── config.py             # Configuration (Qdrant, data dir, API key)
├── requirements.txt
├── README.md
│
├── data/                 # User and sample data files
│   ├── df_Customers.csv
│   ├── df_OrderItems.csv
│   ├── df_Orders.csv
│   ├── df_Payments.csv
│   └── df_Products.csv
│
├── chatwithdb/           # Core application modules (Python package)
│   ├── __init__.py
│   ├── embedder.py
│   ├── metadata_extractor.py
│   ├── qdrant_client_utils.py
│   └── query_parser.py
```

---

## Dependencies

- `streamlit` (web UI)
- `pandas`, `pandasql` (data handling and SQL on DataFrames)
- `sentence-transformers` (for vector embeddings)
- `qdrant-client` (vector database)
- `google-generativeai` (Google Gemini LLM API)
- `python-dotenv` (for `.env` file support)
- See `requirements.txt` for the full list.

---

## Setup & Running

1. **Clone the repository**  
   ```
   git clone <https://github.com/tamerkanak/chatwithDB>
   cd ChatWithDB
   ```

2. **Create a `.env` file in the root directory**  
   ```
   API_KEY=your_gemini_api_key_here
   ```

3. **Install dependencies**  
   ```
   pip install -r requirements.txt
   ```

4. **Start Qdrant vector database**  
   (Recommended: use Docker)
   ```
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

5. **Run the Streamlit app**  
   ```
   streamlit run app.py
   ```

6. **(Optional) Use the CLI**  
   ```
   python main.py
   ```

---

## Usage

1. Open the Streamlit web app in your browser.
2. Upload your CSV/XLSX files.
3. Click "Start Indexing" to process and embed your tables.
4. Enter natural language questions about your data and get instant answers, SQL, and summaries.

---

## Notes

- **API Key Security**: Never share your Gemini API key.
- **Data Privacy**: Uploaded files are processed locally.
- **Extensibility**: You can add new embedding models, LLMs, or database backends by extending the relevant modules.

---

## Credits

Developed by [Tamer Kanak](https://github.com/tamerkanak)  
[LinkedIn](https://www.linkedin.com/in/tamerkanak/) 
