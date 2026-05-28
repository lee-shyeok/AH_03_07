from celery.signals import worker_init

from ai_worker.core.celery_app import celery_app  # noqa: F401 — worker 진입점
from ai_worker.core.qdrant_init import ensure_collection_exists, get_qdrant_client


@worker_init.connect
def init_qdrant_collection(**kwargs: object) -> None:
    client = get_qdrant_client()
    ensure_collection_exists(client)
