from datetime import datetime, time, timedelta

from app.core import config
from app.models.medical_schedule import MedicalSchedule, MedicalScheduleType
from app.models.notifications import NotificationType
from app.repositories.notification_repository import NotificationRepository

SCHEDULE_LABELS: dict[MedicalScheduleType, str] = {
    MedicalScheduleType.BLOOD_TEST: "정기 혈액검사",
    MedicalScheduleType.URINE_TEST: "소변검사",
    MedicalScheduleType.EYE_EXAM: "안과검진",
    MedicalScheduleType.APPOINTMENT: "외래 진료",
    MedicalScheduleType.INJECTION: "주사 투여",
}


class ScheduleReminderService:
    def __init__(self) -> None:
        self.notification_repository = NotificationRepository()

    async def create_reminder_for_schedule(self, schedule: MedicalSchedule) -> None:
        label = SCHEDULE_LABELS[schedule.schedule_type]
        remind_date = schedule.scheduled_date - timedelta(days=schedule.reminder_days_before)
        # 과거 날짜여도 생성 — scheduled_at NOT NULL 제약 충족, 노출 여부는 알림 레이어가 결정
        scheduled_at = datetime.combine(remind_date, time(9, 0), tzinfo=config.TIMEZONE)
        title = f"[{label}] 일정 안내"
        content = f"등록하신 [{label}] 일정이 내일({schedule.scheduled_date})입니다."
        await self.notification_repository.create_notification(
            user_id=schedule.user_id,
            notification_type=NotificationType.SCHEDULE,
            title=title,
            content=content,
            scheduled_at=scheduled_at,
        )
