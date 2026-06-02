"""REQ-FEED-002 — 주 1회 피드백 집계 및 가명처리 Celery 태스크."""

import asyncio
import datetime
import logging

from tortoise import Tortoise

from ai_worker.core.celery_app import celery_app
from ai_worker.core.config import Config as WorkerConfig

logger = logging.getLogger("ai_worker.feedback_aggregation")

_cfg = WorkerConfig()

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
                "app.models.feedback_logs",
                "app.models.user_consents",
                "app.models.model_improvement_dataset",
                "app.models.audit_log",
                "app.models.users",
            ],
        },
    },
    "timezone": "Asia/Seoul",
}

# 가이드 평점 저조 임계값
_LOW_RATING_THRESHOLD = 3


@celery_app.task(
    bind=True,
    name="ai_worker.tasks.feedback_aggregation_tasks.aggregate_feedback_weekly",
    queue="ml_queue",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def aggregate_feedback_weekly(self) -> None:  # noqa: ANN001
    """주 1회 피드백 집계 → 가명처리 → ModelImprovementDataset 생성."""
    asyncio.run(_aggregate_async())


async def _aggregate_async() -> None:
    await Tortoise.init(config=_TORTOISE_ORM)
    try:
        await _run_aggregation()
    finally:
        await Tortoise.close_connections()


async def _run_aggregation() -> None:
    from app.core.anonymization.pseudonymize import describe_level, pseudonymize_user_id
    from app.models.feedback_logs import FeedbackLog, FeedbackType, TargetType
    from app.models.model_improvement_dataset import ModelImprovementDataset
    from app.models.user_consents import ConsentType, UserConsent

    now = datetime.datetime.now(tz=datetime.UTC)
    # 지난 주 월요일 00:00 ~ 일요일 23:59:59 (UTC)
    days_since_monday = now.weekday()  # 0=월
    week_start = (now - datetime.timedelta(days=days_since_monday + 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + datetime.timedelta(days=7) - datetime.timedelta(seconds=1)

    iso_week = week_start.isocalendar()
    dataset_version = f"{iso_week.year}-W{iso_week.week:02d}"

    # 이미 집계된 버전이면 중복 실행 방지
    if await ModelImprovementDataset.filter(dataset_version=dataset_version).exists():
        logger.info(f"skip: dataset {dataset_version} already exists")
        return

    # MODEL_IMPROVEMENT 동의 사용자 ID 목록
    consented = await UserConsent.filter(
        consent_type=ConsentType.MODEL_IMPROVEMENT,
        agreed=True,
        withdrawn_at=None,
    ).values_list("user_id", flat=True)
    consented_ids = list(consented)

    if not consented_ids:
        logger.info(f"skip: no consented users for {dataset_version}")
        return

    # 가이드 저평점 집계 (rating < threshold, 동의자만)
    low_rated_count = await FeedbackLog.filter(
        target_type=TargetType.GUIDE,
        feedback_type=FeedbackType.RATING,
        rating__lt=_LOW_RATING_THRESHOLD,
        user_id__in=consented_ids,
        created_at__gte=week_start,
        created_at__lte=week_end,
    ).count()

    # OCR 수정 빈도 (REGENERATE = 재처리 요청 = 수정)
    high_ocr_count = await FeedbackLog.filter(
        target_type=TargetType.OCR,
        feedback_type=FeedbackType.REGENERATE,
        user_id__in=consented_ids,
        created_at__gte=week_start,
        created_at__lte=week_end,
    ).count()

    # 챗봇 👎 사례
    thumbs_down_count = await FeedbackLog.filter(
        target_type=TargetType.CHAT,
        feedback_type=FeedbackType.THUMBS_DOWN,
        user_id__in=consented_ids,
        created_at__gte=week_start,
        created_at__lte=week_end,
    ).count()

    total = low_rated_count + high_ocr_count + thumbs_down_count

    # 가명처리 — 사용자 ID 해시 (집계 건수만 저장, 원본 ID 비저장)
    pseudonymization_level = describe_level(user_hashed=True, terms_encrypted=False)
    pseudonymized_ids = [pseudonymize_user_id(str(uid)) for uid in consented_ids]
    del pseudonymized_ids  # 건수만 필요, 목록은 메모리에서 즉시 제거

    dataset = await ModelImprovementDataset.create(
        dataset_version=dataset_version,
        week_start=week_start,
        week_end=week_end,
        low_rated_guide_count=low_rated_count,
        high_ocr_correction_count=high_ocr_count,
        thumbs_down_chat_count=thumbs_down_count,
        total_records=total,
        consent_only=True,
        pseudonymized_at=now,
        pseudonymization_level=pseudonymization_level,
    )

    # 감사 로그 (NFR-COMPLI-004) — 시스템 행위이므로 user_id 없이 기록 불가,
    # user FK required → AuditLog는 건너뛰고 logger로 대체
    logger.info(
        f'{{"event": "feedback_aggregation_done", '
        f'"dataset_version": "{dataset_version}", '
        f'"dataset_id": "{dataset.id}", '
        f'"low_rated": {low_rated_count}, '
        f'"ocr_corrections": {high_ocr_count}, '
        f'"thumbs_down": {thumbs_down_count}, '
        f'"total": {total}, '
        f'"pseudonymization_level": "{pseudonymization_level}"}}'
    )
