"""
진료기록 라우터  REQ-MEDI-001 ~ REQ-MEDI-005
"""

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from medical_record_models import MedicalRecord, Medication
from medical_record_schemas import (
    MedicalRecordBrief,
    MedicalRecordCreate,
    MedicalRecordDetail,
    MedicalRecordListResponse,
    MedicalRecordUpdate,
    MedicationResponse,
)
from ocr_models import MedicalDocument
from security import get_current_user_id

router = APIRouter()

MAX_PAGE_SIZE = 50
MAX_FILTER_LEN = 100


def _get_record_or_404(record_id: int, user_id: int, db: Session) -> MedicalRecord:
    record = (
        db.query(MedicalRecord)
        .filter(
            MedicalRecord.id == record_id,
            MedicalRecord.user_id == user_id,
            MedicalRecord.deleted_at.is_(None),
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="진료 기록을 찾을 수 없습니다.")
    return record


def _build_detail(record: MedicalRecord, medications: list) -> MedicalRecordDetail:
    return MedicalRecordDetail(
        id=record.id,
        visit_date=record.visit_date,
        hospital_name=record.hospital_name,
        diagnosis=record.diagnosis,
        medications=[MedicationResponse.model_validate(m) for m in medications],
        memo=record.memo,
        document_id=record.document_id,
        has_guide=record.has_guide,
        guide_needs_update=record.guide_needs_update,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/medical-records",
    response_model=MedicalRecordDetail,
    status_code=201,
    summary="REQ-MEDI-001: 진료기록 직접 입력",
)
def create_medical_record(
    data: MedicalRecordCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if data.document_id is not None:
        doc = (
            db.query(MedicalDocument)
            .filter(
                MedicalDocument.id == data.document_id,
                MedicalDocument.user_id == user_id,
                MedicalDocument.deleted_at.is_(None),
            )
            .first()
        )
        if not doc:
            raise HTTPException(status_code=404, detail="연결할 문서를 찾을 수 없습니다.")

    record = MedicalRecord(
        user_id=user_id,
        visit_date=data.visit_date,
        hospital_name=data.hospital_name,
        diagnosis=data.diagnosis,
        memo=data.memo,
        document_id=data.document_id,
    )
    db.add(record)

    try:
        db.flush()
        medications = []
        for med in data.medications:
            medication = Medication(
                record_id=record.id,
                drug_name=med.drug_name,
                dosage=med.dosage,
                frequency=med.frequency,
                duration_days=med.duration_days,
                timing=med.timing,
            )
            db.add(medication)
            medications.append(medication)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="진료 기록 저장에 실패했습니다.")

    db.refresh(record)
    for m in medications:
        db.refresh(m)

    return _build_detail(record, medications)


@router.get(
    "/medical-records",
    response_model=MedicalRecordListResponse,
    summary="REQ-MEDI-002: 진료기록 목록 조회",
)
def list_medical_records(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    hospital_name: str | None = Query(None, max_length=MAX_FILTER_LEN),
    diagnosis: str | None = Query(None, max_length=MAX_FILTER_LEN),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(MedicalRecord).filter(
        MedicalRecord.user_id == user_id,
        MedicalRecord.deleted_at.is_(None),
    )

    if date_from:
        query = query.filter(MedicalRecord.visit_date >= date_from)
    if date_to:
        query = query.filter(MedicalRecord.visit_date <= date_to)
    if hospital_name:
        query = query.filter(MedicalRecord.hospital_name.ilike(f"%{hospital_name}%"))
    if diagnosis:
        query = query.filter(MedicalRecord.diagnosis.ilike(f"%{diagnosis}%"))

    if order == "asc":
        query = query.order_by(MedicalRecord.visit_date.asc(), MedicalRecord.id.asc())
    else:
        query = query.order_by(MedicalRecord.visit_date.desc(), MedicalRecord.id.desc())

    total = query.count()
    records = query.offset((page - 1) * size).limit(size).all()

    record_ids = [r.id for r in records]
    med_counts = {}
    if record_ids:
        rows = (
            db.query(Medication.record_id, func.count(Medication.id))
            .filter(Medication.record_id.in_(record_ids))
            .group_by(Medication.record_id)
            .all()
        )
        med_counts = {row[0]: row[1] for row in rows}

    items = [
        MedicalRecordBrief(
            id=r.id,
            visit_date=r.visit_date,
            hospital_name=r.hospital_name,
            diagnosis=r.diagnosis,
            medication_count=med_counts.get(r.id, 0),
            has_guide=r.has_guide,
            guide_needs_update=r.guide_needs_update,
            created_at=r.created_at,
        )
        for r in records
    ]

    return MedicalRecordListResponse(items=items, total=total, page=page, size=size)


@router.get(
    "/medical-records/{record_id}",
    response_model=MedicalRecordDetail,
    summary="REQ-MEDI-003: 진료기록 상세 조회",
)
def get_medical_record(
    record_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    record = _get_record_or_404(record_id, user_id, db)
    medications = db.query(Medication).filter(Medication.record_id == record_id).all()
    return _build_detail(record, medications)


@router.patch(
    "/medical-records/{record_id}",
    response_model=MedicalRecordDetail,
    summary="REQ-MEDI-004: 진료기록 수정",
)
def update_medical_record(
    record_id: int,
    data: MedicalRecordUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    record = _get_record_or_404(record_id, user_id, db)

    if data.visit_date is not None:
        record.visit_date = data.visit_date
    if data.hospital_name is not None:
        record.hospital_name = data.hospital_name
    if data.diagnosis is not None:
        record.diagnosis = data.diagnosis
    if data.memo is not None:
        record.memo = data.memo

    if data.medications is not None:
        db.query(Medication).filter(Medication.record_id == record_id).delete()
        for med in data.medications:
            db.add(
                Medication(
                    record_id=record_id,
                    drug_name=med.drug_name,
                    dosage=med.dosage,
                    frequency=med.frequency,
                    duration_days=med.duration_days,
                    timing=med.timing,
                )
            )
        if record.has_guide:
            record.guide_needs_update = True

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="진료 기록 수정에 실패했습니다.")

    db.refresh(record)
    medications = db.query(Medication).filter(Medication.record_id == record_id).all()
    return _build_detail(record, medications)


@router.delete(
    "/medical-records/{record_id}",
    status_code=204,
    summary="REQ-MEDI-005: 진료기록 삭제",
)
def delete_medical_record(
    record_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    record = _get_record_or_404(record_id, user_id, db)
    now = datetime.now(UTC)
    record.deleted_at = now
    db.query(Medication).filter(Medication.record_id == record_id).delete()
    db.commit()
