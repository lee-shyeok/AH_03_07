"""임베딩 Celery 태스크 테스트.

DB 연결 없이 실행 가능하도록 ORM 모델 작업을 포함한 모든 외부 의존성을 Mock 처리.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import fitz
import pytest

from app.models.knowledge import DocumentStatus, KnowledgeDocument


def _make_minimal_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Rheumatoid arthritis drug treatment guidelines. " * 30, fontsize=12)
    return doc.tobytes()


def _make_mock_doc(doc_id: int = 1, pdf_path: str = "/tmp/test_knowledge.pdf") -> MagicMock:
    """KnowledgeDocument 인스턴스를 모사하는 Mock 객체를 생성한다."""
    doc = MagicMock(spec=KnowledgeDocument)
    doc.id = doc_id
    doc.title = "EULAR 2022 RA 권고안"
    doc.filename = "eular.pdf"
    doc.file_path = pdf_path
    doc.source_organization = "EULAR"
    doc.published_year = 2022
    doc.status = DocumentStatus.PENDING
    doc.chunk_count = None
    doc.error_message = None
    doc.save = AsyncMock()
    doc.refresh_from_db = AsyncMock()
    return doc


@pytest.fixture(autouse=True)
def _write_pdf(tmp_path):
    """각 테스트에서 사용할 실제 PDF 파일을 /tmp에 기록한다."""
    path = "/tmp/test_knowledge.pdf"
    with open(path, "wb") as f:
        f.write(_make_minimal_pdf())
    return path


@patch("ai_worker.tasks.embedding.Tortoise.init", new_callable=AsyncMock)
@patch("ai_worker.tasks.embedding.Tortoise.close_connections", new_callable=AsyncMock)
@patch("ai_worker.tasks.embedding.AsyncOpenAI")
@patch("ai_worker.tasks.embedding.AsyncQdrantClient")
@patch("ai_worker.tasks.embedding.KnowledgeDocument")
@pytest.mark.asyncio
async def test_embed_task_sets_status_done(
    mock_doc_cls: MagicMock,
    mock_qdrant_cls: MagicMock,
    mock_openai_cls: MagicMock,
    mock_close: AsyncMock,
    mock_init: AsyncMock,
) -> None:
    """태스크가 성공하면 DocumentStatus.DONE 과 chunk_count 가 저장돼야 한다."""
    mock_doc = _make_mock_doc()
    mock_doc_cls.get = AsyncMock(return_value=mock_doc)

    mock_openai = mock_openai_cls.return_value
    fake_embedding = MagicMock()
    fake_embedding.embedding = [0.1] * 1536
    mock_openai.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[fake_embedding])
    )

    mock_qdrant = mock_qdrant_cls.return_value
    mock_qdrant.delete = AsyncMock()
    mock_qdrant.upsert = AsyncMock()

    from ai_worker.tasks.embedding import _embed_document_async

    await _embed_document_async(mock_doc.id)

    # save() 가 최소 한 번(DONE 상태 저장) 호출돼야 한다
    assert mock_doc.save.call_count >= 1
    assert mock_doc.status == DocumentStatus.DONE
    assert mock_doc.chunk_count is not None
    assert mock_doc.chunk_count >= 1
    mock_qdrant.upsert.assert_called_once()


@patch("ai_worker.tasks.embedding.Tortoise.init", new_callable=AsyncMock)
@patch("ai_worker.tasks.embedding.Tortoise.close_connections", new_callable=AsyncMock)
@patch("ai_worker.tasks.embedding.AsyncOpenAI")
@patch("ai_worker.tasks.embedding.AsyncQdrantClient")
@patch("ai_worker.tasks.embedding.KnowledgeDocument")
@pytest.mark.asyncio
async def test_embed_task_idempotent_deletes_before_upsert(
    mock_doc_cls: MagicMock,
    mock_qdrant_cls: MagicMock,
    mock_openai_cls: MagicMock,
    mock_close: AsyncMock,
    mock_init: AsyncMock,
) -> None:
    """태스크를 두 번 실행하면 Qdrant delete 도 두 번 호출돼야 한다 (멱등성)."""
    mock_doc = _make_mock_doc()
    mock_doc_cls.get = AsyncMock(return_value=mock_doc)

    mock_openai = mock_openai_cls.return_value
    mock_openai.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
    )
    mock_qdrant = mock_qdrant_cls.return_value
    mock_qdrant.delete = AsyncMock()
    mock_qdrant.upsert = AsyncMock()

    from ai_worker.tasks.embedding import _embed_document_async

    await _embed_document_async(mock_doc.id)
    await _embed_document_async(mock_doc.id)

    assert mock_qdrant.delete.call_count == 2


@patch("ai_worker.tasks.embedding.Tortoise.init", new_callable=AsyncMock)
@patch("ai_worker.tasks.embedding.Tortoise.close_connections", new_callable=AsyncMock)
@patch("ai_worker.tasks.embedding.AsyncOpenAI")
@patch("ai_worker.tasks.embedding.AsyncQdrantClient")
@patch("ai_worker.tasks.embedding.KnowledgeDocument")
@pytest.mark.asyncio
async def test_embed_task_sets_failed_on_openai_error(
    mock_doc_cls: MagicMock,
    mock_qdrant_cls: MagicMock,
    mock_openai_cls: MagicMock,
    mock_close: AsyncMock,
    mock_init: AsyncMock,
) -> None:
    """OpenAI 호출이 실패하면 DocumentStatus.FAILED 와 error_message 가 저장돼야 한다."""
    from openai import OpenAIError

    mock_doc = _make_mock_doc()
    mock_doc_cls.get = AsyncMock(return_value=mock_doc)

    mock_openai = mock_openai_cls.return_value
    mock_openai.embeddings.create = AsyncMock(side_effect=OpenAIError("rate limit"))
    mock_qdrant = mock_qdrant_cls.return_value
    mock_qdrant.delete = AsyncMock()

    from ai_worker.tasks.embedding import _embed_document_async

    with pytest.raises(OpenAIError):
        await _embed_document_async(mock_doc.id)

    assert mock_doc.status == DocumentStatus.FAILED
    assert "rate limit" in (mock_doc.error_message or "")
