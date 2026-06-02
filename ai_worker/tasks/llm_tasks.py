from ai_worker.core.celery_app import celery_app


@celery_app.task(
    bind=True,
    queue="llm_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def run_llm_task(self, session_id: str, prompt: str) -> None:  # noqa: ANN001
    raise NotImplementedError