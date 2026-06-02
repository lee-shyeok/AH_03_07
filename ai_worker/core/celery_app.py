from celery import Celery
from celery.schedules import crontab

from ai_worker.core.config import Config

_config = Config()

celery_app = Celery(
    "ai_worker",
    broker=_config.CELERY_BROKER_URL,
    backend=_config.CELERY_RESULT_BACKEND,
    include=[
        "ai_worker.tasks.embedding",
        "ai_worker.tasks.feedback_aggregation_tasks",  # REQ-FEED-002
    ],
)

celery_app.conf.update(
    worker_concurrency=_config.CELERY_WORKER_CONCURRENCY,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="Asia/Seoul",
    enable_utc=True,
    # REQ-FEED-002: 주 1회 피드백 집계 (매주 월요일 02:00 KST = UTC 17:00 일요일)
    beat_schedule={
        "aggregate-feedback-weekly": {
            "task": "ai_worker.tasks.feedback_aggregation_tasks.aggregate_feedback_weekly",
            "schedule": crontab(hour=17, minute=0, day_of_week=0),
        },
    },
)
