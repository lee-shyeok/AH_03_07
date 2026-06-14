"""REQ-AUTO-005 실 DB 연동 DataSourceCollector 구현체."""

from datetime import datetime, timedelta

from app.core import config
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.lab_result import LabResult
from app.models.medical_schedule import MedicalSchedule
from app.models.risk_flag import RiskFlag, RiskFlagSourceType, RiskFlagStatus
from app.models.symptom_check_log import SymptomCheckLog
from app.models.user_disease import UserDisease
from app.models.user_medication import UserMedication
from app.models.user_risk_profile import PregnancyStatus, UserRiskProfile
from app.models.users import User, UserMode


class DbDataSourceCollector:
    """모든 데이터를 실 DB에서 수집하는 DataSourceCollector 구현체."""

    async def get_autoimmune_mode(self, user_id: int) -> bool:
        user = await User.get_or_none(id=user_id)
        if user is None:
            return False
        return user.mode == UserMode.AUTOIMMUNE

    async def get_disease_codes(self, user_id: int) -> list[str]:
        codes = await UserDisease.filter(user_id=user_id, deleted_at=None).values_list("disease_code", flat=True)
        return list(codes)

    async def get_risk_factor_summary(self, user_id: int) -> str | None:
        profile = await UserRiskProfile.get_or_none(user_id=user_id)
        if profile is None:
            return None
        parts: list[str] = []
        if profile.pregnancy_status != PregnancyStatus.NONE:
            parts.append(f"임신·수유 상태: {profile.pregnancy_status}")
        if profile.renal_impairment:
            parts.append("신장 기능 저하 있음")
        if profile.hepatic_impairment:
            parts.append("간 기능 저하 있음")
        if profile.infection_history:
            parts.append(f"감염 이력: {profile.infection_history}")
        if profile.drug_allergy:
            parts.append(f"약물 알레르기: {profile.drug_allergy}")
        if profile.comorbidities:
            parts.append(f"동반 질환: {profile.comorbidities}")
        return "; ".join(parts) if parts else None

    async def get_medication_list(self, user_id: int) -> list[str]:
        names = await UserMedication.filter(user_id=user_id, deleted_at=None).values_list("name", flat=True)
        return list(names)

    async def get_activity_score_summary(self, user_id: int) -> str | None:
        today = datetime.now(config.TIMEZONE).date()
        start = today - timedelta(days=30)
        logs = await DiseaseActivityLog.filter(user_id=user_id, log_date__gte=start).all()
        if not logs:
            return None
        n = len(logs)
        avg_pain = sum(log.pain_vas for log in logs) / n
        avg_fatigue = sum(log.fatigue for log in logs) / n
        avg_difficulty = sum(log.daily_difficulty for log in logs) / n
        return (
            f"최근 30일 평균 통증 VAS {avg_pain:.1f}, "
            f"피로 {avg_fatigue:.1f}, "
            f"일상 어려움 {avg_difficulty:.1f} "
            f"(총 {n}일 기록)"
        )

    async def get_risk_symptom_codes(self, user_id: int) -> list[str]:
        logs = await SymptomCheckLog.filter(user_id=user_id, red_flag_triggered=True).all()
        codes: set[str] = set()
        for log in logs:
            codes.update(log.checked_symptoms or [])
        return list(codes)

    async def get_upcoming_appointments(self, user_id: int) -> list[str]:
        today = datetime.now(config.TIMEZONE).date()
        schedules = (
            await MedicalSchedule.filter(
                user_id=user_id,
                deleted_at=None,
                scheduled_date__gte=today,
            )
            .order_by("scheduled_date")
            .all()
        )
        return [f"{s.scheduled_date} {s.schedule_type}" for s in schedules]

    async def get_lab_results_summary(self, user_id: int) -> str | None:
        results = await LabResult.filter(user_id=user_id, deleted_at=None).order_by("-test_date").limit(10).all()
        if not results:
            return None
        parts = []
        for r in results:
            entry = f"{r.test_date} {r.test_item}: {r.value}"
            if r.reference_range:
                entry += f" (참고범위: {r.reference_range})"
            parts.append(entry)
        return "; ".join(parts)

    async def get_pregnancy_lactation_codes(self, user_id: int) -> list[str]:
        profile = await UserRiskProfile.get_or_none(user_id=user_id)
        if profile is None:
            return []
        if profile.pregnancy_status in (PregnancyStatus.PREGNANT, PregnancyStatus.BREASTFEEDING):
            return [str(profile.pregnancy_status)]
        return []

    async def get_vaccine_infection_prevention(self, user_id: int) -> str | None:
        profile = await UserRiskProfile.get_or_none(user_id=user_id)
        if profile is None:
            return None
        return profile.infection_history or None

    async def get_checked_symptom_codes(self, user_id: int) -> tuple[list[str], bool]:
        """(코드 목록, is_stale) 반환. 14일 초과 로그는 stale=True."""
        log = await SymptomCheckLog.filter(user_id=user_id).order_by("-created_at").first()
        if log is None:
            return [], False
        cutoff = datetime.now(config.TIMEZONE) - timedelta(days=14)
        is_stale = log.created_at < cutoff
        return list(log.checked_symptoms or []), is_stale

    async def get_self_report_codes(self, user_id: int) -> list[str]:
        flags = await RiskFlag.filter(
            user_id=user_id,
            source_type=RiskFlagSourceType.RISK_PROFILE,
            status=RiskFlagStatus.ACTIVE,
        ).all()
        return [f.flag_code for f in flags]

    async def get_lab_threshold_exceeded(self, user_id: int) -> bool:
        return await RiskFlag.filter(
            user_id=user_id,
            source_type=RiskFlagSourceType.LAB_RESULT,
            status=RiskFlagStatus.ACTIVE,
        ).exists()
