import hashlib
import json
import time
from dataclasses import asdict

import redis.asyncio as aioredis
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from app.core import config
from app.core.logger import default_logger as logger
from app.dtos.knowledge import KnowledgeChunk

_COLLECTION_NAME = "medical_kb"
_CACHE_TTL = 86400  # 24h


def _make_cache_key(query: str, top_k: int) -> str:
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    return f"kb:search:{query_hash}:k{top_k}"


async def search_knowledge(query: str, top_k: int = 5) -> list[KnowledgeChunk]:
    cache_key = _make_cache_key(query, top_k)
    query_hash = cache_key.split(":")[2]

    redis_client = aioredis.from_url(config.REDIS_URL)
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(json.dumps({"event": "kb_search_hit", "query_hash": query_hash, "top_k": top_k}))
            return [KnowledgeChunk(**item) for item in json.loads(cached)]
    except Exception:
        pass  # Redis 장애 시 폴백

    start = time.monotonic()
    openai = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    emb_resp = await openai.embeddings.create(model="text-embedding-3-small", input=query)
    query_vector = emb_resp.data[0].embedding

    qdrant = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    response = await qdrant.query_points(
        collection_name=_COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )
    hits = response.points
    chunks = [
        KnowledgeChunk(
            document_id=h.payload["document_id"],
            chunk_index=h.payload["chunk_index"],
            text=h.payload["text"],
            score=h.score,
            page_number=h.payload["page_number"],
            section_title=h.payload.get("section_title"),
            source_title=h.payload["source_title"],
            source_organization=h.payload["source_organization"],
            published_year=h.payload["published_year"],
        )
        for h in hits
    ]
    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        json.dumps({"event": "kb_search_miss", "query_hash": query_hash, "top_k": top_k, "duration_ms": duration_ms})
    )

    try:
        await redis_client.setex(cache_key, _CACHE_TTL, json.dumps([asdict(c) for c in chunks]))
    except Exception:
        pass  # 캐시 저장 실패는 무시

    return chunks
