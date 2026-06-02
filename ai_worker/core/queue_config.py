from kombu import Queue

QUEUE_NAMES: list[str] = [
    "ocr_queue",
    "llm_queue",
    "ml_queue",
    "notification_queue",
    "content_queue",
]

TASK_QUEUES: list[Queue] = [Queue(name) for name in QUEUE_NAMES]

TASK_ROUTES: dict[str, dict[str, str]] = {
    "ai_worker.tasks.embedding.*": {"queue": "ml_queue"},
    "ai_worker.tasks.ocr_tasks.*": {"queue": "ocr_queue"},
    "ai_worker.tasks.llm_tasks.*": {"queue": "llm_queue"},
    "ai_worker.tasks.ml_tasks.*": {"queue": "ml_queue"},
    "ai_worker.tasks.notification_tasks.*": {"queue": "notification_queue"},
    "ai_worker.tasks.content_tasks.*": {"queue": "content_queue"},
}
