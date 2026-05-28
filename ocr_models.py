import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class DocumentTypeEnum(str, enum.Enum):
    prescription = "prescription"       # 처방전
    medical_record = "medical_record"   # 진료기록
    pill_bag = "pill_bag"               # 약봉투
    lab_result = "lab_result"           # 검사결과지
    health_checkup = "health_checkup"  # 건강검진
    other = "other"                     # 기타


class UploadStatusEnum(str, enum.Enum):
    uploaded = "uploaded"    # 업로드 완료, OCR 미시작
    confirmed = "confirmed"  # 사용자 확정 완료
    deleted = "deleted"      # 삭제됨


class OcrJobStatusEnum(str, enum.Enum):
    pending = "pending"        # 대기 중
    processing = "processing"  # 처리 중
    completed = "completed"    # 완료
    failed = "failed"          # 실패


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    document_type = Column(Enum(DocumentTypeEnum), nullable=False)

    # [보안] 실제 저장 경로는 서버 내부 전용 — 응답에 절대 노출하지 않음
    file_path = Column(String(500), nullable=False)
    # [보안] 원본 파일명은 표시용으로만 사용 (경로/URL 생성에 사용 금지)
    original_filename = Column(String(255), nullable=False)
    # [보안] UUID 기반 내부 파일명 — 파일 다운로드 토큰으로만 사용
    stored_filename = Column(String(100), nullable=False)

    file_size = Column(Integer, nullable=True)   # bytes
    mime_type = Column(String(100), nullable=True)

    upload_status = Column(Enum(UploadStatusEnum), default=UploadStatusEnum.uploaded, nullable=False)
    is_user_confirmed = Column(Boolean, default=False, nullable=False)

    # 확정된 OCR 구조화 데이터 (사용자 검토·수정 후 확정된 최종본)
    confirmed_data = Column(Text, nullable=True)  # JSON

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class OcrJob(Base):
    __tablename__ = "ocr_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("medical_documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(Enum(OcrJobStatusEnum), default=OcrJobStatusEnum.pending, nullable=False)

    # OCR 결과
    raw_text = Column(Text, nullable=True)
    structured_data = Column(Text, nullable=True)   # JSON
    confidence_score = Column(Float, nullable=True)  # 0.0 ~ 1.0
    field_confidences = Column(Text, nullable=True)  # JSON

    error_message = Column(String(500), nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
