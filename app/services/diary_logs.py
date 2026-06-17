from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.dtos.diary_logs import (
    MedicationLogCreateRequest,
    MedicationLogListResponse,
    MedicationLogResponse,
    SymptomLogCreateRequest,
    SymptomLogListResponse,
    SymptomLogResponse,
)
from app.repositories.accessibility_repository import AccessibilityRepository
from app.repositories.diary_log_repository import DiaryLogRepository

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_CONDITION_LABELS = {
    "VERY_BAD": "매우 나쁨",
    "BAD": "나쁨",
    "NORMAL": "보통",
    "GOOD": "좋음",
    "VERY_GOOD": "매우 좋음",
}


class DiaryLogService:
    """일기 (증상 + 복약) 비즈니스 로직"""

    def __init__(self):
        self.repo = DiaryLogRepository()
        self.accessibility_repo = AccessibilityRepository()

    # ========== 증상 기록 ==========
    async def get_symptom_logs(self, user_id: UUID) -> SymptomLogListResponse:
        """증상 기록 이력 조회"""
        logs = await self.repo.get_symptom_logs(user_id)
        return SymptomLogListResponse(
            logs=[SymptomLogResponse.model_validate(log) for log in logs],
            total=len(logs),
        )

    async def create_symptom_log(self, user_id: UUID, data: SymptomLogCreateRequest) -> SymptomLogResponse:
        """증상 기록 생성"""
        new_log = await self.repo.create_symptom_log(
            user_id=user_id,
            log_date=data.log_date,
            overall_condition=data.overall_condition,
            body_parts=data.body_parts,
            feeling=data.feeling,
            memo=data.memo,
            medications=data.medications,
        )
        return SymptomLogResponse.model_validate(new_log)

    async def delete_symptom_log(self, user_id: UUID, log_id: UUID) -> None:
        """증상 기록 삭제"""
        deleted = await self.repo.delete_symptom_log(user_id=user_id, log_id=log_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="기록을 찾을 수 없습니다.")

    # ========== 복약 기록 ==========
    async def get_medication_logs(self, user_id: UUID) -> MedicationLogListResponse:
        """복약 기록 이력 조회"""
        logs = await self.repo.get_medication_logs(user_id)
        return MedicationLogListResponse(
            logs=[MedicationLogResponse.model_validate(log) for log in logs],
            total=len(logs),
        )

    async def create_medication_log(self, user_id: UUID, data: MedicationLogCreateRequest) -> MedicationLogResponse:
        """복약 기록 생성 + NOTI-008 위치 옵션"""
        # NOTI-008: 위치 동의 확인
        latitude = None
        longitude = None
        location_recorded_at = None

        if data.latitude is not None and data.longitude is not None:
            # 사용자의 위치 추적 동의 확인
            setting = await self.accessibility_repo.get_by_user(user_id)
            if setting and setting.location_tracking_enabled:
                latitude = data.latitude
                longitude = data.longitude
                location_recorded_at = datetime.now()

        new_log = await self.repo.create_medication_log(
            user_id=user_id,
            log_date=data.log_date,
            drug_name=data.drug_name,
            taken=data.taken,
            taken_time=data.taken_time,
            notes=data.notes,
            latitude=latitude,
            longitude=longitude,
            location_recorded_at=location_recorded_at,
        )
        return MedicationLogResponse.model_validate(new_log)

    # ========== PDF 출력 ==========
    async def generate_pdf_bytes(self, user_id: UUID) -> bytes:
        """증상·복약 기록 일기 PDF 생성 (REQ-DIARY-001)"""
        symptom_logs = await self.repo.get_symptom_logs(user_id)
        medication_logs = await self.repo.get_medication_logs(user_id)

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        html_str = env.get_template("diary_pdf.html").render(
            symptom_logs=symptom_logs,
            medication_logs=medication_logs,
            generated_at=datetime.now(),
            condition_labels=_CONDITION_LABELS,
        )
        from weasyprint import HTML

        return HTML(string=html_str, base_url=str(_TEMPLATE_DIR)).write_pdf(
            stylesheets=[str(_TEMPLATE_DIR / "pre_consultation_report.css")],
        )
