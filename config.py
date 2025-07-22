import os

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
DATA_DIR = "./data"  # CSV/XLSX files directory
GEMINI_API_KEY = os.environ.get("API_KEY")  # API key is read from environment variable
