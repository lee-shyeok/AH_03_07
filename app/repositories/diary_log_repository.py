from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.models.diary_medication_logs import DiaryMedicationLog
from app.models.diary_symptom_logs import DiarySymptomLog, OverallCondition


class DiaryLogRepository:
    """일기 (증상 + 복약) DB 쿼리 담당"""

    # ========== 증상 기록 ==========

    @staticmethod
    async def get_symptom_logs(user_id: UUID) -> list[DiarySymptomLog]:
        """사용자의 증상 기록 전체 조회"""
        return await DiarySymptomLog.filter(user_id=user_id).order_by("-log_date").all()

    @staticmethod
    async def get_symptom_log_by_date(user_id: UUID, log_date: date) -> DiarySymptomLog | None:
        """특정 날짜 증상 기록 조회"""
        return await DiarySymptomLog.filter(user_id=user_id, log_date=log_date).first()

    @staticmethod
    async def create_symptom_log(
        user_id: UUID,
        log_date: date,
        overall_condition: OverallCondition,
        body_parts: list[str] | None,
        feeling: dict | None,
        memo: str | None,
    ) -> DiarySymptomLog:
        """증상 기록 생성"""
        return await DiarySymptomLog.create(
            user_id=user_id,
            log_date=log_date,
            overall_condition=overall_condition,
            body_parts=body_parts,
            feeling=feeling,
            memo=memo,
        )

    @staticmethod
    async def delete_symptom_log(user_id: UUID, log_id: UUID) -> bool:
        """증상 기록 삭제 — 본인 소유 확인 후 삭제, 없으면 False 반환"""
        deleted_count = await DiarySymptomLog.filter(id=log_id, user_id=user_id).delete()
        return deleted_count > 0

    # ========== 복약 기록 ==========

    @staticmethod
    async def get_medication_logs(user_id: UUID) -> list[DiaryMedicationLog]:
        """사용자의 복약 기록 전체 조회"""
        return await DiaryMedicationLog.filter(user_id=user_id).order_by("-log_date").all()

    @staticmethod
    async def get_medication_logs_by_date(user_id: UUID, log_date: date) -> list[DiaryMedicationLog]:
        """특정 날짜 복약 기록 목록"""
        return await DiaryMedicationLog.filter(user_id=user_id, log_date=log_date).all()

    @staticmethod
    async def create_medication_log(
        user_id: UUID,
        log_date: date,
        drug_name: str,
        taken: bool,
        taken_time: datetime | None = None,
        notes: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        location_recorded_at: datetime | None = None,
    ) -> DiaryMedicationLog:
        """복약 기록 생성 (NOTI-008 위치 태깅 옵션)"""
        return await DiaryMedicationLog.create(
            user_id=user_id,
            log_date=log_date,
            drug_name=drug_name,
            taken=taken,
            taken_time=taken_time,
            notes=notes,
            latitude=latitude,
            longitude=longitude,
            location_recorded_at=location_recorded_at,
        )
