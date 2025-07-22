from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from typing import List, Dict
import config

COLLECTION_NAME = "table_metadata"
VECTOR_SIZE = 1024

class QdrantUtils:
    def __init__(self, url=None, api_key=None):
        self.client = QdrantClient(
            url=url,
            api_key=api_key
        )

    def create_collection(self):
        if COLLECTION_NAME not in [c.name for c in self.client.get_collections().collections]:
            self.client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qdrant_models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=qdrant_models.Distance.COSINE
                )
            )

    def upload_metadata(self, embedding: List[float], metadata: Dict, point_id: int):
        self.client.upload_points(
            collection_name=COLLECTION_NAME,
            points=[
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=metadata
                )
            ]
        )

    def search(self, embedding: List[float], top_k=1):
        hits = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=top_k
        )
        return hits 
