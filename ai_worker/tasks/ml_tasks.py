from ai_worker.core.celery_app import celery_app


@celery_app.task(
    bind=True,
    queue="ml_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def run_ml_inference_task(self, model_id: str, payload: dict) -> None:  # noqa: ANN001
    raise NotImplementedError
