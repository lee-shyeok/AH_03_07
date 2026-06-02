"""NFR-PERF-002 — Celery 큐 분리 정책 단위 테스트."""

from kombu import Queue

# ── queue_config ──────────────────────────────────────────────


def test_queue_names_contains_all_five() -> None:
    from ai_worker.core.queue_config import QUEUE_NAMES

    assert set(QUEUE_NAMES) == {
        "ocr_queue",
        "llm_queue",
        "ml_queue",
        "notification_queue",
        "content_queue",
    }


def test_task_queues_count() -> None:
    from ai_worker.core.queue_config import TASK_QUEUES

    assert len(TASK_QUEUES) == 5


def test_task_queues_are_kombu_queue_instances() -> None:
    from ai_worker.core.queue_config import TASK_QUEUES

    for q in TASK_QUEUES:
        assert isinstance(q, Queue)


def test_task_queues_names_match_queue_names() -> None:
    from ai_worker.core.queue_config import QUEUE_NAMES, TASK_QUEUES

    assert {q.name for q in TASK_QUEUES} == set(QUEUE_NAMES)


def test_task_routes_covers_all_five_queues() -> None:
    from ai_worker.core.queue_config import QUEUE_NAMES, TASK_ROUTES

    routed_queues = {v["queue"] for v in TASK_ROUTES.values()}
    assert routed_queues == set(QUEUE_NAMES)


def test_task_routes_embedding_to_ml_queue() -> None:
    from ai_worker.core.queue_config import TASK_ROUTES

    assert TASK_ROUTES.get("ai_worker.tasks.embedding.*") == {"queue": "ml_queue"}


# ── 태스크 속성 검증 ──────────────────────────────────────────


def test_ocr_task_queue() -> None:
    from ai_worker.tasks.ocr_tasks import process_ocr_task

    assert process_ocr_task.queue == "ocr_queue"


def test_llm_task_queue() -> None:
    from ai_worker.tasks.llm_tasks import run_llm_task

    assert run_llm_task.queue == "llm_queue"


def test_ml_task_queue() -> None:
    from ai_worker.tasks.ml_tasks import run_ml_inference_task

    assert run_ml_inference_task.queue == "ml_queue"


def test_notification_task_queue() -> None:
    from ai_worker.tasks.notification_tasks import send_notification_task

    assert send_notification_task.queue == "notification_queue"


def test_content_task_queue() -> None:
    from ai_worker.tasks.content_tasks import generate_content_task

    assert generate_content_task.queue == "content_queue"


def test_ocr_task_max_retries() -> None:
    from ai_worker.tasks.ocr_tasks import process_ocr_task

    assert process_ocr_task.max_retries == 3


def test_llm_task_max_retries() -> None:
    from ai_worker.tasks.llm_tasks import run_llm_task

    assert run_llm_task.max_retries == 3


def test_ml_task_max_retries() -> None:
    from ai_worker.tasks.ml_tasks import run_ml_inference_task

    assert run_ml_inference_task.max_retries == 3


def test_notification_task_max_retries() -> None:
    from ai_worker.tasks.notification_tasks import send_notification_task

    assert send_notification_task.max_retries == 3


def test_content_task_max_retries() -> None:
    from ai_worker.tasks.content_tasks import generate_content_task

    assert generate_content_task.max_retries == 3


def test_all_tasks_retry_backoff() -> None:
    from ai_worker.tasks.content_tasks import generate_content_task
    from ai_worker.tasks.llm_tasks import run_llm_task
    from ai_worker.tasks.ml_tasks import run_ml_inference_task
    from ai_worker.tasks.notification_tasks import send_notification_task
    from ai_worker.tasks.ocr_tasks import process_ocr_task

    for task in [
        process_ocr_task,
        run_llm_task,
        run_ml_inference_task,
        send_notification_task,
        generate_content_task,
    ]:
        assert task.retry_backoff is True
        assert task.retry_backoff_max == 300