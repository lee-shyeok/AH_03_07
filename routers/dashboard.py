"""
마이페이지 대시보드  REQ-MYPG-001

엔드포인트:
  GET /v1/dashboard   대시보드 데이터 일괄 조회
"""

import json
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from guide_models import Guide, GuideStatusEnum
from medical_record_models import MedicalRecord, Medication
from notification_models import MedicationReminder
from ocr_models import MedicalDocument, OcrJob, OcrJobStatusEnum
from security import get_current_user_id

router = APIRouter()


# ── 헬퍼 ──────────────────────────────────────────────────


def _get_weekday_str(d: date) -> str:
    """date → 요일 문자열 (mon~sun)"""
    return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][d.weekday()]


# ── 응답 스키마 ───────────────────────────────────────────


class DashboardGuideBrief(BaseModel):
    id: int
    record_id: int
    diagnosis: str
    status: str
    created_at: datetime


class DashboardRecordBrief(BaseModel):
    id: int
    visit_date: date
    hospital_name: str | None = None
    diagnosis: str
    medication_count: int


class DashboardOcrJob(BaseModel):
    job_id: int
    document_id: int
    original_filename: str
    ocr_status: str
    created_at: datetime


class DashboardResponse(BaseModel):
    recent_guides: list[DashboardGuideBrief]
    today_medication_reminders_total: int  # 오늘 알림 총 횟수
    today_medication_reminders_remaining: int  # 현재 시각 이후 남은 횟수
    recent_records: list[DashboardRecordBrief]
    pending_ocr_jobs: list[DashboardOcrJob]


# ── 엔드포인트 ────────────────────────────────────────────


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="REQ-MYPG-001: 마이페이지 대시보드",
)
def get_dashboard(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    마이페이지 진입 시 필요한 데이터를 한 번에 반환합니다.
    - 최근 가이드 최대 3개
    - 오늘 복약 알림 (총 횟수 / 현재 시각 이후 남은 횟수)
    - 최근 진료 기록 최대 3개
    - 진행 중인 OCR 작업
    """
    now = datetime.now(UTC)
    today = date.today()
    today_weekday = _get_weekday_str(today)
    current_time_str = now.strftime("%H:%M")

    # ── 1. 최근 가이드 (최대 3개, active + needs_update) ──
    guide_rows = (
        db.query(Guide, MedicalRecord.diagnosis)
        .join(MedicalRecord, Guide.record_id == MedicalRecord.id)
        .filter(
            Guide.user_id == user_id,
            Guide.deleted_at.is_(None),
            Guide.status != GuideStatusEnum.archived,
            MedicalRecord.deleted_at.is_(None),
        )
        .order_by(Guide.created_at.desc())
        .limit(3)
        .all()
    )
    recent_guides = [
        DashboardGuideBrief(
            id=guide.id,
            record_id=guide.record_id,
            diagnosis=diagnosis,
            status=guide.status.value,
            created_at=guide.created_at,
        )
        for guide, diagnosis in guide_rows
    ]

    # ── 2. 오늘의 복약 알림 ───────────────────────────────
    reminders = (
        db.query(MedicationReminder)
        .filter(
            MedicationReminder.user_id == user_id,
            MedicationReminder.is_active == True,
            MedicationReminder.deleted_at.is_(None),
            MedicationReminder.start_date <= today,
        )
        .all()
    )

    today_total = 0
    today_remaining = 0

    for reminder in reminders:
        # 종료일 체크
        if reminder.end_date and reminder.end_date < today:
            continue

        # 요일 체크
        try:
            weekdays = json.loads(reminder.weekdays)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        if not isinstance(weekdays, list) or today_weekday not in weekdays:
            continue

        # 알림 시각 파싱
        try:
            remind_times = json.loads(reminder.remind_times)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        if not isinstance(remind_times, list):
            continue

        today_total += len(remind_times)
        for t in remind_times:
            if isinstance(t, str) and t > current_time_str:
                today_remaining += 1

    # ── 3. 최근 진료 기록 (최대 3개) ─────────────────────
    records = (
        db.query(MedicalRecord)
        .filter(
            MedicalRecord.user_id == user_id,
            MedicalRecord.deleted_at.is_(None),
        )
        .order_by(MedicalRecord.visit_date.desc(), MedicalRecord.id.desc())
        .limit(3)
        .all()
    )

    # N+1 방지: 약품 수 일괄 조회
    record_ids = [r.id for r in records]
    med_counts: dict = {}
    if record_ids:
        rows = (
            db.query(Medication.record_id, func.count(Medication.id))
            .filter(Medication.record_id.in_(record_ids))
            .group_by(Medication.record_id)
            .all()
        )
        med_counts = {row[0]: row[1] for row in rows}

    recent_records = [
        DashboardRecordBrief(
            id=r.id,
            visit_date=r.visit_date,
            hospital_name=r.hospital_name,
            diagnosis=r.diagnosis,
            medication_count=med_counts.get(r.id, 0),
        )
        for r in records
    ]

    # ── 4. 진행 중인 OCR 작업 ────────────────────────────
    ocr_rows = (
        db.query(OcrJob, MedicalDocument.original_filename)
        .join(MedicalDocument, OcrJob.document_id == MedicalDocument.id)
        .filter(
            OcrJob.user_id == user_id,
            OcrJob.status.in_([OcrJobStatusEnum.pending, OcrJobStatusEnum.processing]),
            MedicalDocument.deleted_at.is_(None),
        )
        .order_by(OcrJob.created_at.desc())
        .all()
    )
    pending_ocr_jobs = [
        DashboardOcrJob(
            job_id=job.id,
            document_id=job.document_id,
            original_filename=filename,
            ocr_status=job.status.value,
            created_at=job.created_at,
        )
        for job, filename in ocr_rows
    ]

    return DashboardResponse(
        recent_guides=recent_guides,
        today_medication_reminders_total=today_total,
        today_medication_reminders_remaining=today_remaining,
        recent_records=recent_records,
        pending_ocr_jobs=pending_ocr_jobs,
    )
