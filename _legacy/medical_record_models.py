from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class MedicalRecord(Base):
    """진료 기록"""

    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # OCR에서 생성된 경우 연결 (직접 입력이면 null)
    document_id = Column(Integer, ForeignKey("medical_documents.id"), nullable=True)

    visit_date = Column(Date, nullable=False)
    hospital_name = Column(String(200), nullable=True)
    diagnosis = Column(String(500), nullable=False)
    memo = Column(Text, nullable=True)

    # 가이드 연동 상태
    has_guide = Column(Boolean, default=False, nullable=False)
    guide_needs_update = Column(Boolean, default=False, nullable=False)

    # Soft Delete
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Medication(Base):
    """처방 약품 (진료기록 1:N)"""

    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False, index=True)

    drug_name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=True)  # 복용량 (예: 1정)
    frequency = Column(String(100), nullable=True)  # 복용 횟수 (예: 1일 3회)
    duration_days = Column(Integer, nullable=True)  # 복용 일수
    timing = Column(String(100), nullable=True)  # 복용 시점 (예: 식후 30분)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
