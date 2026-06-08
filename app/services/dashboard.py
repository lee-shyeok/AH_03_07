from datetime import datetime
from uuid import UUID

from app.core import config
from app.dtos.autoimmune_log import ActivityLogResponse
from app.dtos.autoimmune_medical import MedicalScheduleResponse
from app.dtos.dashboard import DashboardResponse
from app.dtos.risk_flag import RiskFlagItem
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.medical_schedule import MedicalSchedule
from app.models.risk_flag import RiskFlag, RiskFlagStatus
from app.services.medications import MedicationService


class DashboardService:
    async def get_dashboard(self, user_id: UUID) -> DashboardResponse:
        medications = await MedicationService().get_my_medications(user_id=user_id)

        # 오늘의 활성도 기록 (있으면 1건 → 홈 ①카드가 "오늘 기록 여부" 판단)
        today = datetime.now(config.TIMEZONE).date()
        today_log = await DiseaseActivityLog.get_or_none(user_id=user_id, log_date=today)
        recent_activity = (
            [ActivityLogResponse.model_validate(today_log).model_dump(mode="json")] if today_log is not None else []
        )

        active_flags = await RiskFlag.filter(user_id=user_id, status=RiskFlagStatus.ACTIVE).order_by("-created_at")
        active_risk_flags = [RiskFlagItem.model_validate(f).model_dump(mode="json") for f in active_flags]

        pending = await MedicalSchedule.filter(
            user_id=user_id,
            scheduled_date__gte=today,
        ).order_by("scheduled_date")
        pending_schedules = [MedicalScheduleResponse.model_validate(s).model_dump(mode="json") for s in pending]

        return DashboardResponse(
            today_medications=medications.medications,
            recent_activity=recent_activity,
            pending_schedules=pending_schedules,
            active_risk_flags=active_risk_flags,
        )
