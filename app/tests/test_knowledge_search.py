import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.dtos.knowledge import KnowledgeChunk
from app.services.knowledge_search import _make_cache_key, search_knowledge


def test_make_cache_key_includes_top_k():
    key5 = _make_cache_key("류마티스 치료", top_k=5)
    key10 = _make_cache_key("류마티스 치료", top_k=10)
    assert key5 != key10
    assert ":k5" in key5
    assert ":k10" in key10


def test_make_cache_key_normalizes_query():
    key1 = _make_cache_key("  류마티스  ", top_k=5)
    key2 = _make_cache_key("류마티스", top_k=5)
    assert key1 == key2


_FAKE_CHUNK = KnowledgeChunk(
    document_id=1,
    chunk_index=0,
    text="메토트렉세이트 치료 내용",
    score=0.92,
    page_number=5,
    section_title="약물 치료",
    source_title="EULAR 2022",
    source_organization="EULAR",
    published_year=2022,
)


@pytest.mark.asyncio
async def test_search_knowledge_cache_hit():
    cached_data = json.dumps([_FAKE_CHUNK.to_dict()])

    with (
        patch("app.services.knowledge_search.aioredis") as mock_redis_module,
        patch("app.services.knowledge_search.AsyncOpenAI"),
        patch("app.services.knowledge_search.AsyncQdrantClient"),
    ):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_data.encode())
        mock_redis_module.from_url.return_value = mock_redis

        result = await search_knowledge("류마티스 치료")

    assert len(result) == 1
    assert result[0].document_id == 1
    assert result[0].score == 0.92


@pytest.mark.asyncio
async def test_search_knowledge_cache_miss_calls_qdrant():
    fake_point = MagicMock()
    fake_point.score = 0.88
    fake_point.payload = {
        "document_id": 2,
        "chunk_index": 1,
        "text": "EULAR 권고안 내용",
        "page_number": 3,
        "section_title": None,
        "source_title": "EULAR 2022",
        "source_organization": "EULAR",
        "published_year": 2022,
    }

    with (
        patch("app.services.knowledge_search.aioredis") as mock_redis_module,
        patch("app.services.knowledge_search.AsyncOpenAI") as mock_openai_cls,
        patch("app.services.knowledge_search.AsyncQdrantClient") as mock_qdrant_cls,
    ):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis

        mock_openai = mock_openai_cls.return_value
        mock_openai.embeddings.create = AsyncMock(return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)]))

        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.query_points = AsyncMock(return_value=MagicMock(points=[fake_point]))

        result = await search_knowledge("EULAR 권고안", top_k=5)

    assert len(result) == 1
    assert result[0].document_id == 2
    mock_qdrant.query_points.assert_called_once()
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_search_knowledge_redis_failure_falls_back_to_qdrant():
    fake_point = MagicMock()
    fake_point.score = 0.75
    fake_point.payload = {
        "document_id": 3,
        "chunk_index": 0,
        "text": "폴백 결과",
        "page_number": 1,
        "section_title": None,
        "source_title": "ACR 2021",
        "source_organization": "ACR",
        "published_year": 2021,
    }

    with (
        patch("app.services.knowledge_search.aioredis") as mock_redis_module,
        patch("app.services.knowledge_search.AsyncOpenAI") as mock_openai_cls,
        patch("app.services.knowledge_search.AsyncQdrantClient") as mock_qdrant_cls,
    ):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_redis_module.from_url.return_value = mock_redis

        mock_openai = mock_openai_cls.return_value
        mock_openai.embeddings.create = AsyncMock(return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)]))
        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.query_points = AsyncMock(return_value=MagicMock(points=[fake_point]))

        result = await search_knowledge("폴백 테스트")

    assert len(result) == 1
    mock_qdrant.query_points.assert_called_once()
