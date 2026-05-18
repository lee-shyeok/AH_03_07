from celery import Celery

from ai_worker.core.config import Config

_config = Config()

celery_app = Celery(
    "ai_worker",
    broker=_config.CELERY_BROKER_URL,
    backend=_config.CELERY_RESULT_BACKEND,
    include=["ai_worker.tasks.embedding"],
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
)
