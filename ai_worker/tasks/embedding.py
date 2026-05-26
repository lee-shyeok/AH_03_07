import asyncio
import time
import uuid

from openai import AsyncOpenAI, OpenAIError
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue, PointStruct
from tortoise import Tortoise

from ai_worker.core.celery_app import celery_app
from ai_worker.core.config import Config as WorkerConfig
from ai_worker.core.logger import setup_logger
from ai_worker.core.qdrant_init import COLLECTION_NAME
from ai_worker.utils.chunker import chunk_text
from ai_worker.utils.pdf_parser import ParsedBlock, detect_section_title, extract_blocks
from app.models.knowledge import DocumentStatus, KnowledgeDocument

logger = setup_logger("ai_worker.embedding")

_cfg = WorkerConfig()

_TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": _cfg.DB_HOST,
                "port": _cfg.DB_PORT,
                "user": _cfg.DB_USER,
                "password": _cfg.DB_PASSWORD,
                "database": _cfg.DB_NAME,
                "connect_timeout": _cfg.DB_CONNECT_TIMEOUT,
                "maxsize": _cfg.DB_CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": ["app.models.knowledge", "app.models.users"],
        },
    },
    "timezone": "Asia/Seoul",
}

_EMBEDDING_BATCH_SIZE = 100


@celery_app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(OpenAIError, UnexpectedResponse, IOError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
)
def embed_document_task(self, doc_id: int) -> None:  # noqa: ANN001
    asyncio.run(_embed_document_async(doc_id))


async def _embed_document_async(doc_id: int) -> None:
    await Tortoise.init(config=_TORTOISE_ORM)
    doc = None
    try:
        doc = await KnowledgeDocument.get(id=doc_id)
        doc.status = DocumentStatus.PROCESSING
        await doc.save(update_fields=["status", "updated_at"])
        logger.info(f'{{"event": "embed_task_start", "doc_id": {doc_id}}}')
        start = time.monotonic()

        from pathlib import Path

        pdf_bytes = Path(doc.file_path).read_bytes()

        blocks = extract_blocks(pdf_bytes)
        avg_font = sum(b.font_size for b in blocks) / len(blocks) if blocks else 0.0

        full_text = " ".join(b.text for b in blocks)
        chunks = chunk_text(full_text)

        chunk_meta = _build_chunk_metadata(chunks, blocks, avg_font)

        openai = AsyncOpenAI(api_key=_cfg.OPENAI_API_KEY)
        embeddings: list[list[float]] = []
        for i in range(0, len(chunks), _EMBEDDING_BATCH_SIZE):
            batch = chunks[i : i + _EMBEDDING_BATCH_SIZE]
            resp = await openai.embeddings.create(model="text-embedding-3-small", input=batch)
            embeddings.extend(e.embedding for e in resp.data)

        qdrant = AsyncQdrantClient(host=_cfg.QDRANT_HOST, port=_cfg.QDRANT_PORT)
        await qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))])
            ),
        )
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}:{meta['chunk_index']}")),
                vector=emb,
                payload={
                    "document_id": doc_id,
                    "chunk_index": meta["chunk_index"],
                    "page_number": meta["page_number"],
                    "section_title": meta["section_title"],
                    "source_title": doc.title,
                    "source_organization": doc.source_organization,
                    "published_year": doc.published_year,
                    "text": chunks[meta["chunk_index"]],
                },
            )
            for meta, emb in zip(chunk_meta, embeddings, strict=False)
        ]
        await qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.DONE
        await doc.save(update_fields=["chunk_count", "status", "updated_at"])
        duration = time.monotonic() - start
        logger.info(
            f'{{"event": "embed_task_done", "doc_id": {doc_id}, "chunk_count": {len(chunks)}, "duration_sec": {duration:.1f}}}'
        )

    except Exception as exc:
        if doc is not None:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)[:2000]
            await doc.save(update_fields=["status", "error_message", "updated_at"])
        logger.error(f'{{"event": "embed_task_failed", "doc_id": {doc_id}, "error": "{exc}"}}')
        raise
    finally:
        await Tortoise.close_connections()


def _build_chunk_metadata(chunks: list[str], blocks: list[ParsedBlock], avg_font: float) -> list[dict]:
    last_section: str | None = None
    result = []
    for i, chunk in enumerate(chunks):
        section = None
        page_num = 1
        for block in blocks:
            if block.text[:40] in chunk:
                page_num = block.page_number
                candidate = detect_section_title(block.text, block.font_size, avg_font)
                if candidate:
                    section = candidate
                    last_section = section
                break
        if section is None:
            section = last_section
        result.append({"chunk_index": i, "section_title": section, "page_number": page_num})
    return result
