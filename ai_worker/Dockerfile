FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --group ai --group app --no-dev --frozen

# FastAPI app 모델 + ai_worker 소스 모두 복사 (TortoiseORM 모델 공유)
COPY ./app ./app
COPY ./ai_worker ./ai_worker

CMD ["uv", "run", "--no-sync", "celery", "-A", "ai_worker.core.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency=2", "--queues=celery,ocr_queue"]
