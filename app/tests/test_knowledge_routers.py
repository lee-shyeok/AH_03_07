import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.security import get_request_user
from app.main import app
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.users import User

_PDF_MAGIC = b"%PDF-1.4 fake pdf content for testing purposes only"


def _make_mock_admin() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = 1
    user.is_admin = True
    return user


def _make_mock_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = 2
    user.is_admin = False
    return user


def _make_mock_doc(doc_id: int = 1, status: DocumentStatus = DocumentStatus.PENDING) -> MagicMock:
    doc = MagicMock(spec=KnowledgeDocument)
    doc.id = doc_id
    doc.title = "EULAR 2022 RA 권고안"
    doc.filename = "eular.pdf"
    doc.file_path = "/tmp/eular.pdf"
    doc.source_organization = "EULAR"
    doc.published_year = 2022
    doc.status = status
    doc.chunk_count = None
    doc.error_message = None
    doc.created_at = None
    doc.updated_at = None
    doc.save = AsyncMock()
    return doc


@pytest.fixture(autouse=True)
def override_auth():
    """Default: admin user. Tests that need non-admin override this fixture."""
    admin = _make_mock_admin()
    app.dependency_overrides[get_request_user] = lambda: admin
    yield admin
    app.dependency_overrides.clear()


@patch("app.apis.v1.knowledge_routers.embed_document_task")
@patch("app.apis.v1.knowledge_routers.KnowledgeDocument")
@pytest.mark.asyncio
async def test_upload_pdf_returns_202(mock_doc_cls: MagicMock, mock_task: MagicMock) -> None:
    mock_doc = _make_mock_doc()
    mock_doc_cls.filter.return_value.exists = AsyncMock(return_value=False)
    mock_doc_cls.create = AsyncMock(return_value=mock_doc)
    mock_task.delay = MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/knowledge-base/documents",
            data={
                "title": "EULAR 2022 RA 권고안",
                "source_organization": "EULAR",
                "published_year": "2022",
            },
            files={"file": ("eular.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
        )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "PENDING"
    mock_task.delay.assert_called_once()


@patch("app.apis.v1.knowledge_routers.embed_document_task")
@patch("app.apis.v1.knowledge_routers.KnowledgeDocument")
@pytest.mark.asyncio
async def test_upload_non_admin_returns_403(mock_doc_cls: MagicMock, mock_task: MagicMock) -> None:
    non_admin = _make_mock_user()
    app.dependency_overrides[get_request_user] = lambda: non_admin

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/knowledge-base/documents",
            data={"title": "테스트", "source_organization": "기관", "published_year": "2020"},
            files={"file": ("test.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
        )
    assert resp.status_code == 403


@patch("app.apis.v1.knowledge_routers.embed_document_task")
@pytest.mark.asyncio
async def test_upload_invalid_pdf_magic_returns_400(mock_task: MagicMock) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/knowledge-base/documents",
            data={"title": "가짜 PDF", "source_organization": "테스트", "published_year": "2022"},
            files={"file": ("fake.pdf", io.BytesIO(b"NOT A PDF"), "application/pdf")},
        )
    assert resp.status_code == 400


@patch("app.apis.v1.knowledge_routers.embed_document_task")
@patch("app.apis.v1.knowledge_routers.KnowledgeDocument")
@pytest.mark.asyncio
async def test_upload_duplicate_returns_409(mock_doc_cls: MagicMock, mock_task: MagicMock) -> None:
    mock_doc_cls.filter.return_value.exists = AsyncMock(return_value=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/knowledge-base/documents",
            data={"title": "중복 문서", "source_organization": "기관", "published_year": "2021"},
            files={"file": ("dup.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
        )
    assert resp.status_code == 409


@patch("app.apis.v1.knowledge_routers.embed_document_task")
@patch("app.apis.v1.knowledge_routers.KnowledgeDocument")
@pytest.mark.asyncio
async def test_retry_failed_document_returns_202(mock_doc_cls: MagicMock, mock_task: MagicMock) -> None:
    failed_doc = _make_mock_doc(doc_id=5, status=DocumentStatus.FAILED)
    mock_doc_cls.get_or_none = AsyncMock(return_value=failed_doc)
    mock_task.delay = MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/admin/knowledge-base/documents/5/retry")
    assert resp.status_code == 202
    mock_task.delay.assert_called_once_with(5)


@patch("app.apis.v1.knowledge_routers.KnowledgeDocument")
@pytest.mark.asyncio
async def test_retry_non_failed_document_returns_409(mock_doc_cls: MagicMock) -> None:
    done_doc = _make_mock_doc(doc_id=6, status=DocumentStatus.DONE)
    mock_doc_cls.get_or_none = AsyncMock(return_value=done_doc)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/admin/knowledge-base/documents/6/retry")
    assert resp.status_code == 409
