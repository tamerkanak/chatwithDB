import os
import streamlit as st

QDRANT_HOST = "00bf48d1-0936-40be-b23c-76b37ea23486.eu-west-2-0.aws.cloud.qdrant.io"
QDRANT_PORT = 6333
QDRANT_API_KEY = st.secrets.get("QDRANT_API_KEY") or os.environ.get("QDRANT_API_KEY")
DATA_DIR = "./data"
GEMINI_API_KEY = st.secrets.get("API_KEY") or os.environ.get("API_KEY") 
