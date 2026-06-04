"""REQ-NOTI-007 — 처방 종료일 D-7·D-3·D-1 알림 생성 Celery beat 태스크.

평일 보정: 알림 발송일이 토·일요일이면 직전 금요일로 앞당긴다.
"""

import asyncio
import datetime
import logging

from tortoise import Tortoise

from ai_worker.core.celery_app import celery_app
from ai_worker.core.config import Config as WorkerConfig

logger = logging.getLogger("ai_worker.prescription_end_alert")

_cfg = WorkerConfig()

_ALERT_DAYS_BEFORE = (7, 3, 1)

_TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": _cfg.DB_HOST,
                "port": _cfg.DB_PORT,
                "user": _cfg.DB_USER,
                "password": _cfg.DB_PASSWORD,
                "database": _cfg.DB_NAME,
                "connect_timeout": _cfg.DB_CONNECT_TIMEOUT,
                "maxsize": _cfg.DB_CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user_medication",
                "app.models.users",
                "app.models.notifications",
            ],
        },
    },
    "timezone": "Asia/Seoul",
}


def _adjust_to_weekday(date: datetime.date) -> datetime.date:
    """토(5)·일(6)이면 직전 금요일(4)로 앞당긴다."""
    weekday = date.weekday()
    if weekday == 5:  # 토요일
        return date - datetime.timedelta(days=1)
    if weekday == 6:  # 일요일
        return date - datetime.timedelta(days=2)
    return date


def compute_alert_dates(end_date: datetime.date) -> dict[int, datetime.date]:
    """D-N 알림 발송일 계산 (평일 보정 포함)."""
    return {days: _adjust_to_weekday(end_date - datetime.timedelta(days=days)) for days in _ALERT_DAYS_BEFORE}


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.prescription_end_alert_tasks.send_prescription_end_alerts",
    queue="notification_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_prescription_end_alerts(self) -> None:  # noqa: ANN001
    """매일 실행: 처방 종료일 D-7·D-3·D-1 대상자에게 알림 생성."""
    asyncio.run(_run_alerts_async())


async def _run_alerts_async() -> None:
    await Tortoise.init(config=_TORTOISE_ORM)
    try:
        await _create_alerts()
    finally:
        await Tortoise.close_connections()


async def _create_alerts() -> None:
    from app.models.notifications import Notification, NotificationType
    from app.models.user_medication import UserMedication

    today = datetime.date.today()

    medications = await UserMedication.filter(
        end_date__isnull=False,
        deleted_at__isnull=True,
    ).select_related("user")

    created_count = 0
    for med in medications:
        if med.end_date is None:
            continue
        alert_dates = compute_alert_dates(med.end_date)
        for days_before, alert_date in alert_dates.items():
            if alert_date != today:
                continue
            scheduled_at = datetime.datetime.combine(today, datetime.time(9, 0))
            await Notification.create(
                user=med.user,
                notification_type=NotificationType.MEDICATION,
                title=f"처방 종료 {days_before}일 전 안내",
                content=(
                    f"'{med.name}' 처방이 {med.end_date.strftime('%Y년 %m월 %d일')}에 종료됩니다. "
                    "담당 의사와 처방 연장 여부를 확인하세요."
                ),
                scheduled_at=scheduled_at,
            )
            created_count += 1
            logger.info(
                f'{{"event":"prescription_end_alert_created","user_id":{med.user_id},'
                f'"medication":"{med.name}","end_date":"{med.end_date}",'
                f'"days_before":{days_before},"alert_date":"{alert_date}"}}'
            )

    logger.info(f'{{"event":"prescription_end_alert_done","created":{created_count},"date":"{today}"}}')
