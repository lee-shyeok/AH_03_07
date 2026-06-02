from ai_worker.core.celery_app import celery_app
from ai_worker.core.queue_config import TASK_QUEUES, TASK_ROUTES

celery_app.conf.update(task_queues=TASK_QUEUES, task_routes=TASK_ROUTES)

import ai_worker.tasks.content_tasks  # noqa: F401, E402
import ai_worker.tasks.feedback_aggregation_tasks  # noqa: F401, E402  REQ-FEED-002
import ai_worker.tasks.llm_tasks  # noqa: F401, E402
import ai_worker.tasks.ml_tasks  # noqa: F401, E402
import ai_worker.tasks.notification_tasks  # noqa: F401, E402
import ai_worker.tasks.ocr_tasks  # noqa: F401, E402
