from ai_worker.core.celery_app import celery_app


@celery_app.task(
    bind=True,
    queue="content_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def generate_content_task(self, template_id: str, context: dict) -> None:  # noqa: ANN001
    raise NotImplementedError
