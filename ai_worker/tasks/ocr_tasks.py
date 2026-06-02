from ai_worker.core.celery_app import celery_app


@celery_app.task(
    bind=True,
    queue="ocr_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def process_ocr_task(self, document_id: int) -> None:  # noqa: ANN001
    raise NotImplementedError
