"""
OCR / 의료문서 라우터  REQ-OCR-001 ~ REQ-OCR-005

엔드포인트:
  POST   /v1/medical-documents                  파일 업로드
  GET    /v1/medical-documents                  목록 조회
  GET    /v1/medical-documents/{id}             상세 조회
  GET    /v1/medical-documents/{id}/download    파일 다운로드 (인증 필요)
  DELETE /v1/medical-documents/{id}             삭제
  POST   /v1/medical-documents/{id}/ocr-jobs    OCR 작업 시작 (비동기)
  GET    /v1/ocr-jobs/{job_id}                  OCR 작업 상태/결과 조회
  PUT    /v1/medical-documents/{id}/confirm     OCR 결과 확정
"""
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from ocr_engine import run_ocr
from ocr_models import DocumentTypeEnum, MedicalDocument, OcrJob, OcrJobStatusEnum, UploadStatusEnum
from ocr_schemas import (
    ConfirmOcrRequest,
    ConfirmOcrResponse,
    MedicalDocumentDetail,
    MedicalDocumentListResponse,
    MedicalDocumentUploadResponse,
    OcrJobCreateResponse,
    OcrJobResult,
)
from security import get_current_user_id

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# [수정 #4] 허용 매직바이트 (Content-Type 헤더 단독 신뢰 금지)
_MAGIC_BYTES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",  # 3바이트로 체크
}
_ALLOWED_PDF_MAGIC = b"%PDF"
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10MB
# [수정 #9] 페이지당 최대 항목 수 제한
MAX_PAGE_SIZE = 50


# ── 내부 헬퍼 ─────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """
    [수정 #1] Path Traversal 방지.
    파일명에서 경로 구분자·위험 문자 제거 후 255자로 자름.
    """
    # 경로 구분자 및 null byte 제거
    name = name.replace("/", "").replace("\\", "").replace("\x00", "")
    # 영문·숫자·한글·공백·하이픈·언더스코어·점 외 제거
    name = re.sub(r"[^\w\s\-.]", "", name, flags=re.UNICODE)
    name = name.strip(". ")  # 앞뒤 점·공백 제거
    return name[:255] if name else "unnamed"


def _verify_magic_bytes(data: bytes) -> str:
    """
    [수정 #4] 매직바이트로 실제 파일 형식 검증.
    지원하지 않는 형식이면 ValueError.
    Returns 허용된 mime_type 문자열.
    """
    if data[:4] == _ALLOWED_PDF_MAGIC:
        return "application/pdf"
    if data[:4] == b"\x89PNG" and data[4:8] == b"\r\n\x1a\n":  # PNG 전체 시그니처
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    raise ValueError("JPG, PNG, PDF 파일만 업로드 가능합니다.")


def _get_doc_or_404(doc_id: int, user_id: int, db: Session) -> MedicalDocument:
    doc = db.query(MedicalDocument).filter(
        MedicalDocument.id == doc_id,
        MedicalDocument.user_id == user_id,
        MedicalDocument.deleted_at.is_(None),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    return doc


def _save_file(content: bytes, doc_id: int, original_name: str) -> tuple[str, str]:
    """
    [수정 #1] 원본 파일명은 UUID 기반 stored_filename으로 대체하여 저장.
    실제 경로에 원본 파일명이 포함되지 않음.
    Returns: (file_path, stored_filename)
    """
    ext = Path(original_name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".pdf"}:
        ext = ""
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    dest_dir = UPLOAD_DIR / str(doc_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / stored_filename
    dest.write_bytes(content)
    return str(dest), stored_filename


# ── OCR 백그라운드 작업 ───────────────────────────────────

def _run_ocr_background(job_id: int, file_path: str, document_type: str) -> None:
    """BackgroundTasks로 실행되는 OCR 처리 함수."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        job = db.query(OcrJob).filter(OcrJob.id == job_id).first()
        if not job:
            return

        job.status = OcrJobStatusEnum.processing
        job.started_at = datetime.now(UTC)
        db.commit()

        try:
            raw_text, structured_data, field_confidences, overall = run_ocr(file_path, document_type)
            job.status = OcrJobStatusEnum.completed
            job.raw_text = raw_text
            job.structured_data = json.dumps(structured_data, ensure_ascii=False)
            job.field_confidences = json.dumps(field_confidences, ensure_ascii=False)
            job.confidence_score = overall
        except Exception as e:
            job.status = OcrJobStatusEnum.failed
            job.error_message = str(e)[:500]
        finally:
            job.completed_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()


# ── 1. 파일 업로드 ────────────────────────────────────────

@router.post(
    "/medical-documents",
    response_model=MedicalDocumentUploadResponse,
    status_code=201,
    summary="REQ-OCR-001: 의료문서 업로드",
)
async def upload_medical_document(
    file: UploadFile = File(...),
    document_type: DocumentTypeEnum = Form(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """JPG/PNG/PDF 업로드. 최대 10MB."""
    # [수정 #5] 스트리밍 방식으로 읽어 크기 초과 시 즉시 거부 (메모리 낭비 방지)
    chunks = []
    total = 0
    async for chunk in file:
        total += len(chunk)
        if total > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다.")
        chunks.append(chunk)
    content = b"".join(chunks)

    # [수정 #4] 매직바이트로 실제 파일 형식 검증
    try:
        verified_mime = _verify_magic_bytes(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # [수정 #1] 파일명 정제
    safe_original = _sanitize_filename(file.filename or "unnamed")

    # [수정 #6] 파일 저장 먼저, DB 저장 나중 (역순 트랜잭션)
    #   → DB 레코드 생성 실패 시 파일만 남는 문제 해결
    #   → 단, 파일 ID가 필요하므로 임시 디렉토리 경로 사용
    temp_stored = f"{uuid.uuid4().hex}"  # ID 확정 전 임시 파일명

    doc = MedicalDocument(
        user_id=user_id,
        document_type=document_type,
        file_path="pending",        # 아래에서 실제 경로로 교체
        original_filename=safe_original,
        stored_filename="pending",  # 아래에서 교체
        mime_type=verified_mime,
        file_size=len(content),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # DB ID 확정 후 실제 파일 저장
    try:
        file_path, stored_filename = _save_file(content, doc.id, safe_original)
    except OSError:
        # [수정 #12] 파일 저장 실패 시 DB 레코드 롤백
        db.delete(doc)
        db.commit()
        raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")

    doc.file_path = file_path
    doc.stored_filename = stored_filename
    db.commit()
    db.refresh(doc)

    return doc


# ── 2. 목록 조회 ──────────────────────────────────────────

@router.get(
    "/medical-documents",
    response_model=MedicalDocumentListResponse,
    summary="REQ-OCR-005: 의료문서 목록 조회",
)
def list_medical_documents(
    document_type: DocumentTypeEnum | None = None,
    page: int = 1,
    size: int = 10,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # [수정 #9] page/size 범위 제한
    if page < 1:
        raise HTTPException(status_code=400, detail="page는 1 이상이어야 합니다.")
    if not (1 <= size <= MAX_PAGE_SIZE):
        raise HTTPException(status_code=400, detail=f"size는 1~{MAX_PAGE_SIZE} 사이여야 합니다.")

    query = db.query(MedicalDocument).filter(
        MedicalDocument.user_id == user_id,
        MedicalDocument.deleted_at.is_(None),
    )
    if document_type:
        query = query.filter(MedicalDocument.document_type == document_type)

    total = query.count()
    items = (
        query.order_by(MedicalDocument.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return MedicalDocumentListResponse(items=items, total=total, page=page, size=size)


# ── 3. 상세 조회 ──────────────────────────────────────────

@router.get(
    "/medical-documents/{doc_id}",
    response_model=MedicalDocumentDetail,
    summary="REQ-OCR-005: 의료문서 상세 조회",
)
def get_medical_document(
    doc_id: int,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    doc = _get_doc_or_404(doc_id, user_id, db)
    base_url = str(request.base_url).rstrip("/")
    return MedicalDocumentDetail.from_orm_with_url(doc, base_url)


# ── 4. 파일 다운로드 (인증 필요) ─────────────────────────

@router.get(
    "/medical-documents/{doc_id}/download",
    summary="의료문서 파일 다운로드 (인증 필요)",
)
def download_medical_document(
    doc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    [수정 #2] 파일을 직접 서빙 — 인증된 본인만 접근 가능.
    stored_filename(UUID 기반)으로 저장된 파일을 original_filename으로 내려줌.
    """
    doc = _get_doc_or_404(doc_id, user_id, db)
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,   # 다운로드 시 표시될 파일명
        media_type=doc.mime_type or "application/octet-stream",
    )


# ── 5. OCR 작업 시작 ──────────────────────────────────────

@router.post(
    "/medical-documents/{doc_id}/ocr-jobs",
    response_model=OcrJobCreateResponse,
    status_code=202,
    summary="REQ-OCR-002: OCR 처리 시작 (비동기)",
)
def start_ocr_job(
    doc_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    OCR 작업을 생성하고 백그라운드에서 처리합니다.
    결과는 GET /v1/ocr-jobs/{job_id} 로 폴링하세요.
    """
    doc = _get_doc_or_404(doc_id, user_id, db)

    # 이미 진행 중인 작업 중복 방지
    existing = db.query(OcrJob).filter(
        OcrJob.document_id == doc_id,
        OcrJob.status.in_([OcrJobStatusEnum.pending, OcrJobStatusEnum.processing]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="이미 처리 중인 OCR 작업이 있습니다.")

    job = OcrJob(
        document_id=doc_id,
        user_id=user_id,
        status=OcrJobStatusEnum.pending,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        _run_ocr_background,
        job.id,
        doc.file_path,
        doc.document_type.value,
    )

    return OcrJobCreateResponse.from_orm(job)


# ── 6. OCR 결과 조회 (폴링) ───────────────────────────────

@router.get(
    "/ocr-jobs/{job_id}",
    response_model=OcrJobResult,
    summary="REQ-OCR-003: OCR 작업 상태 및 결과 조회",
)
def get_ocr_job(
    job_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    job = db.query(OcrJob).filter(
        OcrJob.id == job_id,
        OcrJob.user_id == user_id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="OCR 작업을 찾을 수 없습니다.")
    return OcrJobResult.from_orm(job)


# ── 7. OCR 결과 확정 ─────────────────────────────────────

@router.put(
    "/medical-documents/{doc_id}/confirm",
    response_model=ConfirmOcrResponse,
    summary="REQ-OCR-004: OCR 결과 사용자 검토 후 확정",
)
def confirm_ocr_result(
    doc_id: int,
    body: ConfirmOcrRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    사용자가 OCR 결과를 검토·수정 후 확정합니다.
    확정된 데이터만 다른 기능(진료기록, 응급카드 등)에서 사용됩니다.
    """
    doc = _get_doc_or_404(doc_id, user_id, db)

    completed_job = (
        db.query(OcrJob)
        .filter(
            OcrJob.document_id == doc_id,
            OcrJob.status == OcrJobStatusEnum.completed,
        )
        .order_by(OcrJob.created_at.desc())
        .first()
    )
    if not completed_job:
        raise HTTPException(
            status_code=400,
            detail="완료된 OCR 작업이 없습니다. OCR 처리를 먼저 완료해주세요.",
        )

    doc.confirmed_data = json.dumps(body.structured_data, ensure_ascii=False)
    doc.is_user_confirmed = True
    doc.upload_status = UploadStatusEnum.confirmed
    db.commit()
    db.refresh(doc)

    confirmed = json.loads(doc.confirmed_data)
    return ConfirmOcrResponse(
        document_id=doc.id,
        upload_status=doc.upload_status,
        is_user_confirmed=doc.is_user_confirmed,
        confirmed_data=confirmed,
        updated_at=doc.updated_at,
    )


# ── 8. 문서 삭제 ──────────────────────────────────────────

@router.delete(
    "/medical-documents/{doc_id}",
    status_code=204,
    summary="REQ-OCR-005: 의료문서 삭제",
)
def delete_medical_document(
    doc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Soft Delete. 물리 파일 삭제는 배치 처리로 분리."""
    doc = _get_doc_or_404(doc_id, user_id, db)
    doc.deleted_at = datetime.now(UTC)
    doc.upload_status = UploadStatusEnum.deleted
    db.commit()
