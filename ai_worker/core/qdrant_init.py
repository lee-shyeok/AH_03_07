from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorsConfig

from ai_worker.core.config import Config

COLLECTION_NAME = "medical_kb"
VECTOR_SIZE = 1536  # text-embedding-3-small


def get_qdrant_client() -> QdrantClient:
    cfg = Config()
    return QdrantClient(host=cfg.QDRANT_HOST, port=cfg.QDRANT_PORT)


def ensure_collection_exists(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorsConfig(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
