import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from ai_worker.tasks.embedding import embed_document_task
from app.core import config
from app.core.logger import default_logger as logger
from app.dependencies.pdf_validator import validate_pdf_upload
from app.dependencies.security import get_request_user
from app.dtos.knowledge import KnowledgeDocumentResponse, KnowledgeDocumentUploadResponse
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.users import User

knowledge_router = APIRouter(prefix="/admin/knowledge-base", tags=["knowledge-base"])


def _require_admin(user: Annotated[User, Depends(get_request_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return user


@knowledge_router.post("/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_knowledge_document(
    admin: Annotated[User, Depends(_require_admin)],
    file: UploadFile,
    title: Annotated[str, Form(max_length=200)],
    source_organization: Annotated[str, Form(max_length=100)],
    published_year: Annotated[int, Form(ge=1950, le=2030)],
) -> KnowledgeDocumentUploadResponse:
    content = await validate_pdf_upload(file)

    exists = await KnowledgeDocument.filter(
        title=title, source_organization=source_organization, published_year=published_year
    ).exists()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 문서입니다.")

    doc = await KnowledgeDocument.create(
        title=title,
        filename=file.filename or "document.pdf",
        file_path="",
        source_organization=source_organization,
        published_year=published_year,
        uploaded_by_user=admin,
    )

    save_dir = Path(config.MEDIA_DIR) / "knowledge" / str(doc.id)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / (file.filename or "document.pdf")
    file_path.write_bytes(content)

    doc.file_path = str(file_path)
    await doc.save(update_fields=["file_path", "updated_at"])

    logger.info(
        f'{{"event": "kb_upload_received", "doc_id": {doc.id}, "title": "{title}", "size_bytes": {len(content)}}}'
    )
    embed_document_task.delay(doc.id)

    return KnowledgeDocumentUploadResponse(document_id=doc.id, title=doc.title, status=doc.status)


@knowledge_router.get("/documents", status_code=status.HTTP_200_OK)
async def list_knowledge_documents(
    admin: Annotated[User, Depends(_require_admin)],
) -> list[KnowledgeDocumentResponse]:
    docs = await KnowledgeDocument.all().order_by("-created_at")
    return [KnowledgeDocumentResponse.model_validate(d) for d in docs]


@knowledge_router.get("/documents/{doc_id}", status_code=status.HTTP_200_OK)
async def get_knowledge_document(
    doc_id: int,
    admin: Annotated[User, Depends(_require_admin)],
) -> KnowledgeDocumentResponse:
    doc = await KnowledgeDocument.get_or_none(id=doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문서를 찾을 수 없습니다.")
    return KnowledgeDocumentResponse.model_validate(doc)


@knowledge_router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_document(
    doc_id: int,
    admin: Annotated[User, Depends(_require_admin)],
) -> None:
    doc = await KnowledgeDocument.get_or_none(id=doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문서를 찾을 수 없습니다.")

    try:
        qdrant = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        await qdrant.delete(
            collection_name="medical_kb",
            points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]),
        )
        logger.info(json.dumps({"event": "kb_qdrant_delete", "doc_id": doc_id}))
    except Exception as exc:
        logger.error(json.dumps({"event": "kb_qdrant_delete_error", "doc_id": doc_id, "error": str(exc)}))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"벡터 스토어 삭제 실패: {exc}",
        ) from exc

    if doc.file_path and Path(doc.file_path).exists():
        Path(doc.file_path).unlink()
    await doc.delete()


@knowledge_router.post("/documents/{doc_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_knowledge_document(
    doc_id: int,
    admin: Annotated[User, Depends(_require_admin)],
) -> KnowledgeDocumentUploadResponse:
    doc = await KnowledgeDocument.get_or_none(id=doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문서를 찾을 수 없습니다.")
    if doc.status != DocumentStatus.FAILED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="현재 상태에서 재처리할 수 없습니다.")

    doc.status = DocumentStatus.PENDING
    doc.error_message = None
    await doc.save(update_fields=["status", "error_message", "updated_at"])
    embed_document_task.delay(doc.id)

    return KnowledgeDocumentUploadResponse(document_id=doc.id, title=doc.title, status=doc.status)
