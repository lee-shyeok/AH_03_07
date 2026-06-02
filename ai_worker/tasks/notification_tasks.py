from ai_worker.core.celery_app import celery_app


@celery_app.task(
    bind=True,
    queue="notification_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def send_notification_task(self, user_id: int, message: str) -> None:  # noqa: ANN001
    raise NotImplementedError