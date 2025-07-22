from sentence_transformers import SentenceTransformer
from typing import List

MODEL_NAME = "BAAI/bge-m3"

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)

    def embed_metadata(self, metadata_text: str) -> List[float]:
        prompt = f"Represent this metadata for retrieval: {metadata_text}"
        embedding = self.model.encode(prompt, normalize_embeddings=True)
        return embedding.tolist()

    def embed_query(self, query: str) -> List[float]:
        prompt = f"Represent this metadata for retrieval: {query}"
        embedding = self.model.encode(prompt, normalize_embeddings=True)
        return embedding.tolist() 