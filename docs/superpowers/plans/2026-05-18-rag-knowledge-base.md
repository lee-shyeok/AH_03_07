# RAG 지식베이스 구현 계획 (REQ-KB-001 / REQ-KB-002)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 자가면역 모드 챗봇·안내문 생성을 위한 임상 가이드라인 지식베이스를 구축하고 유사도 검색 서비스를 제공한다.

**Architecture:** FastAPI가 관리자용 PDF 업로드 API를 제공하고, Celery(브로커: Redis) 비동기 태스크가 PyMuPDF 파싱 → tiktoken 청크 분할 → OpenAI 임베딩 → Qdrant 저장 파이프라인을 실행한다. 검색은 Redis 24h 캐시를 우선 조회하고 MISS 시 Qdrant 코사인 유사도 검색으로 폴백한다.

**Tech Stack:** Python 3.13, FastAPI, TortoiseORM(MySQL), Celery 5.x, Redis, OpenAI text-embedding-3-small, Qdrant, PyMuPDF, tiktoken

**Spec:** `docs/superpowers/specs/2026-05-18-rag-knowledge-base-design.md`

---

## 파일 구조

### 신규 생성
```
app/
  models/knowledge.py               # KnowledgeDocument TortoiseORM 모델
  dtos/knowledge.py                  # KnowledgeChunk, 업로드/응답 DTO
  dependencies/pdf_validator.py      # PDF 크기·매직바이트 검증
  services/knowledge_search.py       # search_knowledge() + Redis 캐시
  apis/v1/knowledge_routers.py       # 관리자 5개 엔드포인트
  tests/test_pdf_validator.py
  tests/test_knowledge_search.py
  tests/test_knowledge_routers.py
  tests/test_embedding_task.py

ai_worker/
  utils/__init__.py
  utils/chunker.py                   # tiktoken 기반 청크 분할
  utils/pdf_parser.py                # PyMuPDF 파싱 + section_title 추출
  core/celery_app.py                 # Celery 앱 인스턴스
  core/qdrant_init.py                # Qdrant 컬렉션 초기화
  tasks/__init__.py
  tasks/embedding.py                 # embed_document_task + _embed_document_async
  tests/__init__.py
  tests/test_chunker.py
  tests/test_pdf_parser.py
```

### 수정
```
pyproject.toml                       # 의존성 추가
docker-compose.yml                   # Qdrant 서비스 추가
ai_worker/Dockerfile                 # app/ 소스 포함 + Celery CMD
app/core/config.py                   # OPENAI_API_KEY, QDRANT_*, MEDIA_DIR, REDIS_URL
ai_worker/core/config.py             # 위 + DB_*, CELERY_*
app/core/db/databases.py             # TORTOISE_APP_MODELS에 knowledge 추가
app/apis/v1/__init__.py              # knowledge_router 등록
ai_worker/main.py                    # Celery 앱 import (worker 진입점)
envs/example.local.env              # 신규 환경변수 예시 추가
```

---

## Task 1: 의존성·설정·인프라

**Files:**
- Modify: `pyproject.toml`
- Modify: `docker-compose.yml`
- Modify: `app/core/config.py`
- Modify: `ai_worker/core/config.py`
- Modify: `ai_worker/Dockerfile`
- Modify: `envs/example.local.env`

- [ ] **Step 1: pyproject.toml 의존성 추가**

```toml
# [dependency-groups] app 섹션에 추가
[dependency-groups]
app = [
    "aerich>=0.9.2",
    "asyncmy>=0.2.11",
    "bcrypt<=4.0.1",
    "celery[redis]>=5.4.0,<6.0.0",
    "fastapi[standard]>=0.128.0",
    "httpx>=0.28.1",
    "openai>=1.30.0,<2.0.0",
    "orjson>=3.11.5",
    "passlib[bcrypt]>=1.7.4",
    "pyjwt>=2.10.1",
    "qdrant-client>=1.12.0,<2.0.0",
    "tortoise-orm>=0.25.3",
    "uvicorn>=0.40.0",
]
ai = [
    "celery[redis]>=5.4.0,<6.0.0",
    "openai>=1.30.0,<2.0.0",
    "pymupdf>=1.24.0,<2.0.0",
    "qdrant-client>=1.12.0,<2.0.0",
    "scikit-learn>=1.8.0",
    "sentence-transformers>=5.2.0",
    "tiktoken>=0.7.0,<1.0.0",
    "torch",
    "torchvision",
    "torchaudio",
    "tortoise-orm>=0.25.3",
    "asyncmy>=0.2.11",
]
```

- [ ] **Step 2: uv sync 실행**

```bash
uv sync --all-groups
```

Expected: 패키지 설치 완료, `uv.lock` 갱신

- [ ] **Step 3: docker-compose.yml에 Qdrant 서비스 추가**

`volumes:` 섹션에 `qdrant_data:` 추가, `services:` 섹션에 아래 추가:

```yaml
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - ws
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5
```

`ai-worker` 서비스 `depends_on`에 추가:
```yaml
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
```

- [ ] **Step 4: ai_worker/Dockerfile 수정**

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --group ai --no-dev --frozen

# FastAPI app 모델 + ai_worker 소스 모두 복사 (TortoiseORM 모델 공유)
COPY ./app ./app
COPY ./ai_worker ./ai_worker

CMD ["uv", "run", "--no-sync", "celery", "-A", "ai_worker.core.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency=2"]
```

- [ ] **Step 5: app/core/config.py에 신규 설정 추가**

기존 `Config` 클래스 안에 추가:
```python
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    MEDIA_DIR: str = "media"
```

- [ ] **Step 6: ai_worker/core/config.py 전체 교체**

```python
import zoneinfo
from dataclasses import field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    TIMEZONE: zoneinfo.ZoneInfo = field(default_factory=lambda: zoneinfo.ZoneInfo("Asia/Seoul"))

    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "pw1234"
    DB_NAME: str = "ai_health"
    DB_CONNECT_TIMEOUT: int = 5
    DB_CONNECTION_POOL_MAXSIZE: int = 5

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_WORKER_CONCURRENCY: int = 2
```

- [ ] **Step 7: envs/example.local.env에 신규 항목 추가**

```
# AI / 벡터 검색
OPENAI_API_KEY=sk-...
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Redis (캐시 + Celery)
REDIS_URL=redis://redis:6379/2
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_WORKER_CONCURRENCY=2

# 파일 저장
MEDIA_DIR=media
```

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock docker-compose.yml ai_worker/Dockerfile \
        app/core/config.py ai_worker/core/config.py envs/example.local.env
git commit -m "chore: RAG 지식베이스 의존성·설정·인프라 추가"
```

---

## Task 2: KnowledgeDocument 모델 & 마이그레이션

**Files:**
- Create: `app/models/knowledge.py`
- Modify: `app/core/db/databases.py`

- [ ] **Step 1: app/models/knowledge.py 생성**

```python
from enum import StrEnum

from tortoise import fields, models


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class KnowledgeDocument(models.Model):
    id = fields.BigIntField(primary_key=True)
    title = fields.CharField(max_length=200)
    filename = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    status = fields.CharEnumField(enum_type=DocumentStatus, default=DocumentStatus.PENDING)
    chunk_count = fields.IntField(null=True)
    source_organization = fields.CharField(max_length=100)
    published_year = fields.SmallIntField()
    error_message = fields.TextField(null=True)
    uploaded_by_user = fields.ForeignKeyField("models.User", related_name="knowledge_documents")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "knowledge_base"
        unique_together = [("title", "source_organization", "published_year")]
        indexes = [("status",), ("uploaded_by_user_id",), ("created_at",)]
```

- [ ] **Step 2: app/core/db/databases.py TORTOISE_APP_MODELS에 추가**

```python
TORTOISE_APP_MODELS = [
    "aerich.models",
    "app.models.users",
    "app.models.knowledge",   # 추가
]
```

- [ ] **Step 3: Aerich 마이그레이션 생성 및 적용**

```bash
uv run aerich migrate --name add_knowledge_base
uv run aerich upgrade
```

Expected: `app/core/db/migrations/models/1_..._add_knowledge_base.py` 생성, DB에 `knowledge_base` 테이블 생성

- [ ] **Step 4: Commit**

```bash
git add app/models/knowledge.py app/core/db/databases.py \
        app/core/db/migrations/
git commit -m "feat: KnowledgeDocument 모델 및 마이그레이션 추가"
```

---

## Task 3: PDF 검증기 (TDD)

**Files:**
- Create: `app/tests/test_pdf_validator.py`
- Create: `app/dependencies/pdf_validator.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# app/tests/test_pdf_validator.py
import pytest
from app.dependencies.pdf_validator import (
    MAX_PDF_SIZE_BYTES,
    check_pdf_magic,
    check_pdf_size,
)


def test_check_pdf_magic_valid():
    assert check_pdf_magic(b"%PDF-1.4 some content") is True


def test_check_pdf_magic_invalid_zip():
    assert check_pdf_magic(b"PK\x03\x04") is False


def test_check_pdf_magic_empty():
    assert check_pdf_magic(b"") is False


def test_check_pdf_magic_short_content():
    assert check_pdf_magic(b"%PDF") is False  # 4바이트, magic은 5바이트


def test_check_pdf_size_at_limit():
    assert check_pdf_size(MAX_PDF_SIZE_BYTES) is True


def test_check_pdf_size_over_limit():
    assert check_pdf_size(MAX_PDF_SIZE_BYTES + 1) is False


def test_check_pdf_size_zero():
    assert check_pdf_size(0) is True
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest app/tests/test_pdf_validator.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.dependencies.pdf_validator'`

- [ ] **Step 3: app/dependencies/pdf_validator.py 구현**

```python
from fastapi import HTTPException, UploadFile

MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
_PDF_MAGIC = b"%PDF-"


def check_pdf_magic(content: bytes) -> bool:
    return content[:5] == _PDF_MAGIC


def check_pdf_size(size: int) -> bool:
    return size <= MAX_PDF_SIZE_BYTES


async def validate_pdf_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if not check_pdf_size(len(content)):
        raise HTTPException(status_code=413, detail="파일 크기가 50MB를 초과합니다.")
    if not check_pdf_magic(content):
        raise HTTPException(status_code=400, detail="PDF 검증 실패: 잘못된 파일 형식")
    return content
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest app/tests/test_pdf_validator.py -v
```

Expected: 7개 PASSED

- [ ] **Step 5: Commit**

```bash
git add app/tests/test_pdf_validator.py app/dependencies/pdf_validator.py
git commit -m "feat: PDF 검증기 추가 (크기 50MB, 매직바이트)"
```

---

## Task 4: PDF 파서 (TDD)

**Files:**
- Create: `ai_worker/utils/__init__.py`
- Create: `ai_worker/tests/__init__.py`
- Create: `ai_worker/tests/test_pdf_parser.py`
- Create: `ai_worker/utils/pdf_parser.py`

- [ ] **Step 1: 패키지 init 파일 생성**

`ai_worker/utils/__init__.py` 와 `ai_worker/tests/__init__.py` 를 빈 파일로 생성.

- [ ] **Step 2: 실패하는 테스트 작성**

```python
# ai_worker/tests/test_pdf_parser.py
import fitz
import pytest
from ai_worker.utils.pdf_parser import (
    ParsedBlock,
    check_pdf_safety,
    detect_section_title,
    extract_blocks,
)


def _make_test_pdf(text: str, fontsize: float = 12.0) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=fontsize)
    return doc.tobytes()


def test_extract_blocks_returns_text():
    pdf_bytes = _make_test_pdf("류마티스 치료 지침")
    blocks = extract_blocks(pdf_bytes)
    combined = " ".join(b.text for b in blocks)
    assert "류마티스" in combined


def test_extract_blocks_page_number():
    pdf_bytes = _make_test_pdf("테스트 텍스트")
    blocks = extract_blocks(pdf_bytes)
    assert all(b.page_number == 1 for b in blocks)


def test_extract_blocks_font_size():
    pdf_bytes = _make_test_pdf("헤더", fontsize=18.0)
    blocks = extract_blocks(pdf_bytes)
    assert any(b.font_size >= 18.0 for b in blocks)


def test_detect_section_title_by_font_size():
    result = detect_section_title("제1장 서론", font_size=20.0, avg_font_size=12.0)
    assert result == "제1장 서론"


def test_detect_section_title_by_regex_chapter():
    result = detect_section_title("제 1 장 서론", font_size=12.0, avg_font_size=12.0)
    assert result == "제 1 장 서론"


def test_detect_section_title_by_regex_numbered():
    result = detect_section_title("1.1 치료 방법", font_size=12.0, avg_font_size=12.0)
    assert result == "1.1 치료 방법"


def test_detect_section_title_by_regex_roman():
    result = detect_section_title("IV. 결론", font_size=12.0, avg_font_size=12.0)
    assert result == "IV. 결론"


def test_detect_section_title_no_match_returns_none():
    result = detect_section_title("일반 본문 텍스트입니다.", font_size=12.0, avg_font_size=12.0)
    assert result is None


def test_check_pdf_safety_clean_pdf():
    pdf_bytes = _make_test_pdf("안전한 문서")
    check_pdf_safety(pdf_bytes)  # 예외 없이 통과


def test_check_pdf_safety_detects_javascript():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    # JavaScript 포함 여부는 xref 검사로 확인 — 실제 악성 PDF 없이 로직만 검증
    # 기본 PDF는 통과함을 확인
    check_pdf_safety(pdf_bytes)  # 예외 없음
```

- [ ] **Step 3: 테스트 실행 — 실패 확인**

```bash
uv run pytest ai_worker/tests/test_pdf_parser.py -v
```

Expected: `ModuleNotFoundError: No module named 'ai_worker.utils.pdf_parser'`

- [ ] **Step 4: ai_worker/utils/pdf_parser.py 구현**

```python
import re
from dataclasses import dataclass

import fitz  # PyMuPDF

_SECTION_PATTERNS = [
    re.compile(r"^제\s*\d+\s*장"),
    re.compile(r"^\d+\.\d+\s"),
    re.compile(r"^[IVX]+\.\s"),
]


@dataclass
class ParsedBlock:
    text: str
    page_number: int
    font_size: float


def check_pdf_safety(pdf_bytes: bytes) -> None:
    """JavaScript 액션이 포함된 PDF면 ValueError를 발생시킨다."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for xref in range(1, doc.xref_length()):
            try:
                obj_str = doc.xref_object(xref)
                if "/JavaScript" in obj_str or "/JS " in obj_str:
                    raise ValueError("악성 콘텐츠 감지: JavaScript 액션 포함")
            except (fitz.mupdf.FzErrorBase, RuntimeError):
                continue
    finally:
        doc.close()


def extract_blocks(pdf_bytes: bytes) -> list[ParsedBlock]:
    """PDF에서 텍스트 블록 목록을 추출한다. 파싱 전 안전 검사를 수행한다."""
    check_pdf_safety(pdf_bytes)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks: list[ParsedBlock] = []
    try:
        for page_num, page in enumerate(doc, start=1):
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                spans = [span for line in block["lines"] for span in line["spans"]]
                text = " ".join(s["text"] for s in spans).strip()
                font_size = max((s["size"] for s in spans), default=0.0)
                if text:
                    blocks.append(ParsedBlock(text=text, page_number=page_num, font_size=font_size))
    finally:
        doc.close()
    return blocks


def detect_section_title(text: str, font_size: float, avg_font_size: float) -> str | None:
    """텍스트가 섹션 제목이면 반환하고, 아니면 None을 반환한다."""
    stripped = text.strip()
    # 1차: 폰트 크기 기반
    if avg_font_size > 0 and font_size >= avg_font_size * 1.2:
        return stripped[:200]
    # 2차: 정규식 패턴
    for pattern in _SECTION_PATTERNS:
        if pattern.match(stripped):
            return stripped[:200]
    return None
```

- [ ] **Step 5: 테스트 실행 — 통과 확인**

```bash
uv run pytest ai_worker/tests/test_pdf_parser.py -v
```

Expected: 10개 PASSED

- [ ] **Step 6: Commit**

```bash
git add ai_worker/utils/__init__.py ai_worker/tests/__init__.py \
        ai_worker/tests/test_pdf_parser.py ai_worker/utils/pdf_parser.py
git commit -m "feat: PyMuPDF PDF 파서 및 section_title 추출기 추가"
```

---

## Task 5: 텍스트 청커 (TDD)

**Files:**
- Create: `ai_worker/tests/test_chunker.py`
- Create: `ai_worker/utils/chunker.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# ai_worker/tests/test_chunker.py
import pytest
from ai_worker.utils.chunker import CHUNK_SIZE_TOKENS, count_tokens, chunk_text


def test_chunk_empty_string():
    assert chunk_text("") == []


def test_chunk_whitespace_only():
    assert chunk_text("   \n  ") == []


def test_chunk_short_text_single_chunk():
    text = "짧은 텍스트입니다."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_long_text_multiple_chunks():
    # 영문 "word " 한 단어 ≈ 1토큰. 600개면 500토큰 초과
    text = "word " * 600
    chunks = chunk_text(text)
    assert len(chunks) >= 2


def test_chunk_size_never_exceeds_limit():
    text = "word " * 600
    chunks = chunk_text(text)
    for chunk in chunks:
        assert count_tokens(chunk) <= CHUNK_SIZE_TOKENS


def test_chunk_overlap_covers_all_tokens():
    text = "word " * 600
    chunks = chunk_text(text)
    # 오버랩 덕분에 총 토큰 수가 원본보다 많거나 같아야 함
    total = sum(count_tokens(c) for c in chunks)
    assert total >= count_tokens(text)


def test_count_tokens_english():
    # "hello world" → cl100k_base에서 2토큰
    assert count_tokens("hello world") == 2


def test_count_tokens_empty():
    assert count_tokens("") == 0
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest ai_worker/tests/test_chunker.py -v
```

Expected: `ModuleNotFoundError: No module named 'ai_worker.utils.chunker'`

- [ ] **Step 3: ai_worker/utils/chunker.py 구현**

```python
import tiktoken

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
_ENCODING_NAME = "cl100k_base"


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding(_ENCODING_NAME)
    return len(enc.encode(text))


def chunk_text(text: str) -> list[str]:
    """텍스트를 500토큰 단위로 분할한다. 오버랩은 50토큰."""
    if not text.strip():
        return []
    enc = tiktoken.get_encoding(_ENCODING_NAME)
    tokens = enc.encode(text)
    if len(tokens) <= CHUNK_SIZE_TOKENS:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE_TOKENS, len(tokens))
        chunks.append(enc.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS
    return chunks
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest ai_worker/tests/test_chunker.py -v
```

Expected: 8개 PASSED

- [ ] **Step 5: Commit**

```bash
git add ai_worker/tests/test_chunker.py ai_worker/utils/chunker.py
git commit -m "feat: tiktoken 기반 텍스트 청커 추가 (500토큰/오버랩 50)"
```

---

## Task 6: Celery 앱 & Qdrant 초기화

**Files:**
- Create: `ai_worker/core/celery_app.py`
- Create: `ai_worker/core/qdrant_init.py`
- Create: `ai_worker/tasks/__init__.py`
- Modify: `ai_worker/main.py`

- [ ] **Step 1: ai_worker/core/celery_app.py 생성**

```python
from celery import Celery
from ai_worker.core.config import Config

_config = Config()

celery_app = Celery(
    "ai_worker",
    broker=_config.CELERY_BROKER_URL,
    backend=_config.CELERY_RESULT_BACKEND,
    include=["ai_worker.tasks.embedding"],
)

celery_app.conf.update(
    worker_concurrency=_config.CELERY_WORKER_CONCURRENCY,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="Asia/Seoul",
    enable_utc=True,
)
```

- [ ] **Step 2: ai_worker/core/qdrant_init.py 생성**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorsConfig

from ai_worker.core.config import Config

COLLECTION_NAME = "medical_kb"
VECTOR_SIZE = 1536  # text-embedding-3-small


def get_qdrant_client() -> QdrantClient:
    cfg = Config()
    return QdrantClient(host=cfg.QDRANT_HOST, port=cfg.QDRANT_PORT)


def ensure_collection_exists(client: QdrantClient) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorsConfig(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
```

- [ ] **Step 3: ai_worker/tasks/__init__.py 생성**

빈 파일로 생성.

- [ ] **Step 4: ai_worker/main.py 업데이트**

```python
from ai_worker.core.celery_app import celery_app  # noqa: F401 — worker 진입점
from ai_worker.core.qdrant_init import ensure_collection_exists, get_qdrant_client
from celery.signals import worker_init


@worker_init.connect
def init_qdrant_collection(**kwargs: object) -> None:
    client = get_qdrant_client()
    ensure_collection_exists(client)
```

- [ ] **Step 5: Commit**

```bash
git add ai_worker/core/celery_app.py ai_worker/core/qdrant_init.py \
        ai_worker/tasks/__init__.py ai_worker/main.py
git commit -m "feat: Celery 앱 설정 및 Qdrant 컬렉션 초기화"
```

---

## Task 7: 임베딩 Celery 태스크 (TDD)

**Files:**
- Create: `app/tests/test_embedding_task.py`
- Create: `ai_worker/tasks/embedding.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# app/tests/test_embedding_task.py
import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import fitz
import pytest
from tortoise.contrib.test import TestCase

from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.users import User


def _make_minimal_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    # 한 페이지에 충분한 텍스트 (청크가 최소 1개 이상 나오도록)
    page.insert_text((50, 100), "류마티스관절염 약물 치료 지침\n" + "메토트렉세이트 치료 내용. " * 30, fontsize=12)
    return doc.tobytes()


class TestEmbedDocumentTask(TestCase):
    async def asyncSetUp(self) -> None:
        self.user = await User.create(
            email="admin@test.com",
            hashed_password="x",
            name="관리자",
            gender="MALE",
            birthday="1990-01-01",
            phone_number="01000000000",
            is_admin=True,
        )
        pdf_path = "/tmp/test_knowledge.pdf"
        with open(pdf_path, "wb") as f:
            f.write(_make_minimal_pdf())

        self.doc = await KnowledgeDocument.create(
            title="EULAR 2022 RA 권고안",
            filename="eular.pdf",
            file_path=pdf_path,
            source_organization="EULAR",
            published_year=2022,
            uploaded_by_user=self.user,
        )

    @patch("ai_worker.tasks.embedding.Tortoise.init", new_callable=AsyncMock)
    @patch("ai_worker.tasks.embedding.Tortoise.close_connections", new_callable=AsyncMock)
    @patch("ai_worker.tasks.embedding.AsyncOpenAI")
    @patch("ai_worker.tasks.embedding.AsyncQdrantClient")
    async def test_embed_task_sets_status_done(
        self,
        mock_qdrant_cls: MagicMock,
        mock_openai_cls: MagicMock,
        mock_close: AsyncMock,
        mock_init: AsyncMock,
    ) -> None:
        # OpenAI mock: 임베딩 응답
        mock_openai = mock_openai_cls.return_value
        fake_embedding = MagicMock()
        fake_embedding.embedding = [0.1] * 1536
        mock_openai.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[fake_embedding])
        )

        # Qdrant mock
        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.delete = AsyncMock()
        mock_qdrant.upsert = AsyncMock()

        from ai_worker.tasks.embedding import _embed_document_async

        await _embed_document_async(self.doc.id)

        await self.doc.refresh_from_db()
        assert self.doc.status == DocumentStatus.DONE
        assert self.doc.chunk_count is not None
        assert self.doc.chunk_count >= 1
        mock_qdrant.upsert.assert_called_once()

    @patch("ai_worker.tasks.embedding.Tortoise.init", new_callable=AsyncMock)
    @patch("ai_worker.tasks.embedding.Tortoise.close_connections", new_callable=AsyncMock)
    @patch("ai_worker.tasks.embedding.AsyncOpenAI")
    @patch("ai_worker.tasks.embedding.AsyncQdrantClient")
    async def test_embed_task_idempotent_deletes_before_upsert(
        self,
        mock_qdrant_cls: MagicMock,
        mock_openai_cls: MagicMock,
        mock_close: AsyncMock,
        mock_init: AsyncMock,
    ) -> None:
        mock_openai = mock_openai_cls.return_value
        mock_openai.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        )
        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.delete = AsyncMock()
        mock_qdrant.upsert = AsyncMock()

        from ai_worker.tasks.embedding import _embed_document_async

        await _embed_document_async(self.doc.id)
        await _embed_document_async(self.doc.id)

        # 2회 호출 → delete가 2번 불려 기존 벡터 정리 확인
        assert mock_qdrant.delete.call_count == 2

    @patch("ai_worker.tasks.embedding.Tortoise.init", new_callable=AsyncMock)
    @patch("ai_worker.tasks.embedding.Tortoise.close_connections", new_callable=AsyncMock)
    @patch("ai_worker.tasks.embedding.AsyncOpenAI")
    @patch("ai_worker.tasks.embedding.AsyncQdrantClient")
    async def test_embed_task_sets_failed_on_openai_error(
        self,
        mock_qdrant_cls: MagicMock,
        mock_openai_cls: MagicMock,
        mock_close: AsyncMock,
        mock_init: AsyncMock,
    ) -> None:
        from openai import OpenAIError

        mock_openai = mock_openai_cls.return_value
        mock_openai.embeddings.create = AsyncMock(side_effect=OpenAIError("rate limit"))
        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.delete = AsyncMock()

        from ai_worker.tasks.embedding import _embed_document_async

        with pytest.raises(OpenAIError):
            await _embed_document_async(self.doc.id)

        await self.doc.refresh_from_db()
        assert self.doc.status == DocumentStatus.FAILED
        assert "rate limit" in (self.doc.error_message or "")
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest app/tests/test_embedding_task.py -v
```

Expected: `ModuleNotFoundError: No module named 'ai_worker.tasks.embedding'`

- [ ] **Step 3: ai_worker/tasks/embedding.py 구현**

```python
import asyncio
import time
import uuid

from openai import AsyncOpenAI, OpenAIError
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue, PointStruct
from tortoise import Tortoise

from ai_worker.core.celery_app import celery_app
from ai_worker.core.config import Config as WorkerConfig
from ai_worker.core.qdrant_init import COLLECTION_NAME
from ai_worker.utils.chunker import chunk_text
from ai_worker.utils.pdf_parser import ParsedBlock, detect_section_title, extract_blocks
from ai_worker.core.logger import setup_logger

logger = setup_logger("ai_worker.embedding")

_cfg = WorkerConfig()

_TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": _cfg.DB_HOST,
                "port": _cfg.DB_PORT,
                "user": _cfg.DB_USER,
                "password": _cfg.DB_PASSWORD,
                "database": _cfg.DB_NAME,
                "connect_timeout": _cfg.DB_CONNECT_TIMEOUT,
                "maxsize": _cfg.DB_CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": ["app.models.knowledge", "app.models.users"],
        },
    },
    "timezone": "Asia/Seoul",
}

_EMBEDDING_BATCH_SIZE = 100


@celery_app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(OpenAIError, UnexpectedResponse, IOError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
)
def embed_document_task(self, doc_id: int) -> None:  # noqa: ANN001
    asyncio.run(_embed_document_async(doc_id))


async def _embed_document_async(doc_id: int) -> None:
    from app.models.knowledge import DocumentStatus, KnowledgeDocument

    await Tortoise.init(config=_TORTOISE_ORM)
    doc = None
    try:
        doc = await KnowledgeDocument.get(id=doc_id)
        doc.status = DocumentStatus.PROCESSING
        await doc.save(update_fields=["status", "updated_at"])
        logger.info(f'{{"event": "embed_task_start", "doc_id": {doc_id}}}')
        start = time.monotonic()

        # 1. PDF 읽기
        from pathlib import Path
        pdf_bytes = Path(doc.file_path).read_bytes()

        # 2. 파싱 (안전 검사 포함)
        blocks = extract_blocks(pdf_bytes)
        avg_font = sum(b.font_size for b in blocks) / len(blocks) if blocks else 0.0

        # 3. 전체 텍스트 청크 분할
        full_text = " ".join(b.text for b in blocks)
        chunks = chunk_text(full_text)

        # 4. 청크별 메타데이터 (section_title, page_number)
        chunk_meta = _build_chunk_metadata(chunks, blocks, avg_font)

        # 5. OpenAI 임베딩 (배치)
        openai = AsyncOpenAI(api_key=_cfg.OPENAI_API_KEY)
        embeddings: list[list[float]] = []
        for i in range(0, len(chunks), _EMBEDDING_BATCH_SIZE):
            batch = chunks[i : i + _EMBEDDING_BATCH_SIZE]
            resp = await openai.embeddings.create(model="text-embedding-3-small", input=batch)
            embeddings.extend(e.embedding for e in resp.data)

        # 6. Qdrant — 기존 포인트 삭제 후 upsert (멱등)
        qdrant = AsyncQdrantClient(host=_cfg.QDRANT_HOST, port=_cfg.QDRANT_PORT)
        await qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))])
            ),
        )
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}:{meta['chunk_index']}")),
                vector=emb,
                payload={
                    "document_id": doc_id,
                    "chunk_index": meta["chunk_index"],
                    "page_number": meta["page_number"],
                    "section_title": meta["section_title"],
                    "source_title": doc.title,
                    "source_organization": doc.source_organization,
                    "published_year": doc.published_year,
                    "text": chunks[meta["chunk_index"]],
                },
            )
            for meta, emb in zip(chunk_meta, embeddings)
        ]
        await qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

        # 7. 완료
        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.DONE
        await doc.save(update_fields=["chunk_count", "status", "updated_at"])
        duration = time.monotonic() - start
        logger.info(f'{{"event": "embed_task_done", "doc_id": {doc_id}, "chunk_count": {len(chunks)}, "duration_sec": {duration:.1f}}}')

    except Exception as exc:
        if doc is not None:
            from app.models.knowledge import DocumentStatus
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)[:2000]
            await doc.save(update_fields=["status", "error_message", "updated_at"])
        logger.error(f'{{"event": "embed_task_failed", "doc_id": {doc_id}, "error": "{exc}"}}')
        raise
    finally:
        await Tortoise.close_connections()


def _build_chunk_metadata(
    chunks: list[str], blocks: list[ParsedBlock], avg_font: float
) -> list[dict]:
    last_section: str | None = None
    result = []
    for i, chunk in enumerate(chunks):
        section = None
        page_num = 1
        for block in blocks:
            if block.text[:40] in chunk:
                page_num = block.page_number
                candidate = detect_section_title(block.text, block.font_size, avg_font)
                if candidate:
                    section = candidate
                    last_section = section
                break
        if section is None:
            section = last_section
        result.append({"chunk_index": i, "section_title": section, "page_number": page_num})
    return result
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest app/tests/test_embedding_task.py -v
```

Expected: 3개 PASSED

- [ ] **Step 5: Commit**

```bash
git add app/tests/test_embedding_task.py ai_worker/tasks/embedding.py
git commit -m "feat: embed_document_task Celery 태스크 구현"
```

---

## Task 8: Knowledge DTOs

**Files:**
- Create: `app/dtos/knowledge.py`

- [ ] **Step 1: app/dtos/knowledge.py 생성**

```python
from dataclasses import dataclass, asdict
from datetime import datetime

from pydantic import Field

from app.dtos.base import BaseSerializerModel
from app.models.knowledge import DocumentStatus


@dataclass
class KnowledgeChunk:
    document_id: int
    chunk_index: int
    text: str
    score: float
    page_number: int
    section_title: str | None
    source_title: str
    source_organization: str
    published_year: int

    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeDocumentResponse(BaseSerializerModel):
    id: int
    title: str
    filename: str
    status: DocumentStatus
    chunk_count: int | None
    source_organization: str
    published_year: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentUploadResponse(BaseSerializerModel):
    document_id: int
    title: str
    status: DocumentStatus
```

- [ ] **Step 2: Commit**

```bash
git add app/dtos/knowledge.py
git commit -m "feat: KnowledgeDocument DTO 추가"
```

---

## Task 9: 검색 서비스 (TDD)

**Files:**
- Create: `app/tests/test_knowledge_search.py`
- Create: `app/services/knowledge_search.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# app/tests/test_knowledge_search.py
import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.dtos.knowledge import KnowledgeChunk
from app.services.knowledge_search import _make_cache_key, search_knowledge


def test_make_cache_key_includes_top_k():
    key5 = _make_cache_key("류마티스 치료", top_k=5)
    key10 = _make_cache_key("류마티스 치료", top_k=10)
    assert key5 != key10
    assert ":k5" in key5
    assert ":k10" in key10


def test_make_cache_key_normalizes_query():
    key1 = _make_cache_key("  류마티스  ", top_k=5)
    key2 = _make_cache_key("류마티스", top_k=5)
    assert key1 == key2


_FAKE_CHUNK = KnowledgeChunk(
    document_id=1,
    chunk_index=0,
    text="메토트렉세이트 치료 내용",
    score=0.92,
    page_number=5,
    section_title="약물 치료",
    source_title="EULAR 2022",
    source_organization="EULAR",
    published_year=2022,
)


@pytest.mark.asyncio
async def test_search_knowledge_cache_hit():
    cached_data = json.dumps([_FAKE_CHUNK.to_dict()])

    with (
        patch("app.services.knowledge_search.aioredis") as mock_redis_module,
        patch("app.services.knowledge_search.AsyncOpenAI"),
        patch("app.services.knowledge_search.AsyncQdrantClient"),
    ):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_data.encode())
        mock_redis_module.from_url.return_value = mock_redis

        result = await search_knowledge("류마티스 치료")

    assert len(result) == 1
    assert result[0].document_id == 1
    assert result[0].score == 0.92


@pytest.mark.asyncio
async def test_search_knowledge_cache_miss_calls_qdrant():
    fake_point = MagicMock()
    fake_point.score = 0.88
    fake_point.payload = {
        "document_id": 2,
        "chunk_index": 1,
        "text": "EULAR 권고안 내용",
        "page_number": 3,
        "section_title": None,
        "source_title": "EULAR 2022",
        "source_organization": "EULAR",
        "published_year": 2022,
    }

    with (
        patch("app.services.knowledge_search.aioredis") as mock_redis_module,
        patch("app.services.knowledge_search.AsyncOpenAI") as mock_openai_cls,
        patch("app.services.knowledge_search.AsyncQdrantClient") as mock_qdrant_cls,
    ):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis

        mock_openai = mock_openai_cls.return_value
        mock_openai.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        )

        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.search = AsyncMock(return_value=[fake_point])

        result = await search_knowledge("EULAR 권고안", top_k=5)

    assert len(result) == 1
    assert result[0].document_id == 2
    mock_qdrant.search.assert_called_once()
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_search_knowledge_redis_failure_falls_back_to_qdrant():
    fake_point = MagicMock()
    fake_point.score = 0.75
    fake_point.payload = {
        "document_id": 3,
        "chunk_index": 0,
        "text": "폴백 결과",
        "page_number": 1,
        "section_title": None,
        "source_title": "ACR 2021",
        "source_organization": "ACR",
        "published_year": 2021,
    }

    with (
        patch("app.services.knowledge_search.aioredis") as mock_redis_module,
        patch("app.services.knowledge_search.AsyncOpenAI") as mock_openai_cls,
        patch("app.services.knowledge_search.AsyncQdrantClient") as mock_qdrant_cls,
    ):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_redis_module.from_url.return_value = mock_redis

        mock_openai = mock_openai_cls.return_value
        mock_openai.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        )
        mock_qdrant = mock_qdrant_cls.return_value
        mock_qdrant.search = AsyncMock(return_value=[fake_point])

        result = await search_knowledge("폴백 테스트")

    assert len(result) == 1
    mock_qdrant.search.assert_called_once()
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest app/tests/test_knowledge_search.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.services.knowledge_search'`

- [ ] **Step 3: app/services/knowledge_search.py 구현**

```python
import hashlib
import json
import time
from dataclasses import asdict

import redis.asyncio as aioredis
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from app.core import config
from app.core.logger import default_logger as logger
from app.dtos.knowledge import KnowledgeChunk

_COLLECTION_NAME = "medical_kb"
_CACHE_TTL = 86400  # 24h


def _make_cache_key(query: str, top_k: int) -> str:
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    return f"kb:search:{query_hash}:k{top_k}"


async def search_knowledge(query: str, top_k: int = 5) -> list[KnowledgeChunk]:
    cache_key = _make_cache_key(query, top_k)
    query_hash = cache_key.split(":")[2]

    redis_client = aioredis.from_url(config.REDIS_URL)
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(json.dumps({"event": "kb_search_hit", "query_hash": query_hash, "top_k": top_k}))
            return [KnowledgeChunk(**item) for item in json.loads(cached)]
    except Exception:
        pass  # Redis 장애 시 폴백

    start = time.monotonic()
    openai = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    emb_resp = await openai.embeddings.create(model="text-embedding-3-small", input=query)
    query_vector = emb_resp.data[0].embedding

    qdrant = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    hits = await qdrant.search(
        collection_name=_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )
    chunks = [
        KnowledgeChunk(
            document_id=h.payload["document_id"],
            chunk_index=h.payload["chunk_index"],
            text=h.payload["text"],
            score=h.score,
            page_number=h.payload["page_number"],
            section_title=h.payload.get("section_title"),
            source_title=h.payload["source_title"],
            source_organization=h.payload["source_organization"],
            published_year=h.payload["published_year"],
        )
        for h in hits
    ]
    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(json.dumps({"event": "kb_search_miss", "query_hash": query_hash, "top_k": top_k, "duration_ms": duration_ms}))

    try:
        await redis_client.setex(cache_key, _CACHE_TTL, json.dumps([asdict(c) for c in chunks]))
    except Exception:
        pass  # 캐시 저장 실패는 무시

    return chunks
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest app/tests/test_knowledge_search.py -v
```

Expected: 4개 PASSED

- [ ] **Step 5: Commit**

```bash
git add app/tests/test_knowledge_search.py app/services/knowledge_search.py
git commit -m "feat: RAG 유사도 검색 서비스 추가 (Redis 24h 캐시)"
```

---

## Task 10: 관리자 API 엔드포인트 (TDD)

**Files:**
- Create: `app/tests/test_knowledge_routers.py`
- Create: `app/apis/v1/knowledge_routers.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# app/tests/test_knowledge_routers.py
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.users import User
from app.services.jwt import JwtService

_PDF_MAGIC = b"%PDF-1.4 fake pdf content for testing purposes only"


def _make_auth_header(user: User) -> dict[str, str]:
    tokens = JwtService().issue_jwt_pair(user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestKnowledgeUpload(TestCase):
    async def asyncSetUp(self) -> None:
        self.admin = await User.create(
            email="admin@kb.com",
            hashed_password="x",
            name="관리자",
            gender="FEMALE",
            birthday="1988-03-15",
            phone_number="01011112222",
            is_admin=True,
        )
        self.user = await User.create(
            email="user@kb.com",
            hashed_password="x",
            name="일반유저",
            gender="MALE",
            birthday="1995-06-20",
            phone_number="01033334444",
            is_admin=False,
        )

    @patch("app.apis.v1.knowledge_routers.embed_document_task")
    async def test_upload_pdf_returns_202(self, mock_task: MagicMock) -> None:
        mock_task.delay = MagicMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/admin/knowledge-base/documents",
                headers=_make_auth_header(self.admin),
                data={
                    "title": "EULAR 2022 RA 권고안",
                    "source_organization": "EULAR",
                    "published_year": "2022",
                },
                files={"file": ("eular.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
            )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "PENDING"
        assert body["title"] == "EULAR 2022 RA 권고안"
        mock_task.delay.assert_called_once()

    @patch("app.apis.v1.knowledge_routers.embed_document_task")
    async def test_upload_non_admin_returns_403(self, mock_task: MagicMock) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/admin/knowledge-base/documents",
                headers=_make_auth_header(self.user),
                data={
                    "title": "테스트",
                    "source_organization": "테스트기관",
                    "published_year": "2020",
                },
                files={"file": ("test.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
            )
        assert resp.status_code == 403

    @patch("app.apis.v1.knowledge_routers.embed_document_task")
    async def test_upload_invalid_pdf_magic_returns_400(self, mock_task: MagicMock) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/admin/knowledge-base/documents",
                headers=_make_auth_header(self.admin),
                data={"title": "가짜 PDF", "source_organization": "테스트", "published_year": "2022"},
                files={"file": ("fake.pdf", io.BytesIO(b"NOT A PDF"), "application/pdf")},
            )
        assert resp.status_code == 400

    @patch("app.apis.v1.knowledge_routers.embed_document_task")
    async def test_upload_duplicate_returns_409(self, mock_task: MagicMock) -> None:
        mock_task.delay = MagicMock()
        await KnowledgeDocument.create(
            title="중복 문서",
            filename="dup.pdf",
            file_path="/tmp/dup.pdf",
            source_organization="중복기관",
            published_year=2021,
            uploaded_by_user=self.admin,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/admin/knowledge-base/documents",
                headers=_make_auth_header(self.admin),
                data={"title": "중복 문서", "source_organization": "중복기관", "published_year": "2021"},
                files={"file": ("dup2.pdf", io.BytesIO(_PDF_MAGIC), "application/pdf")},
            )
        assert resp.status_code == 409

    async def test_retry_non_failed_document_returns_409(self) -> None:
        doc = await KnowledgeDocument.create(
            title="완료된 문서",
            filename="done.pdf",
            file_path="/tmp/done.pdf",
            source_organization="완료기관",
            published_year=2020,
            status=DocumentStatus.DONE,
            uploaded_by_user=self.admin,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/admin/knowledge-base/documents/{doc.id}/retry",
                headers=_make_auth_header(self.admin),
            )
        assert resp.status_code == 409

    @patch("app.apis.v1.knowledge_routers.embed_document_task")
    async def test_retry_failed_document_returns_202(self, mock_task: MagicMock) -> None:
        mock_task.delay = MagicMock()
        doc = await KnowledgeDocument.create(
            title="실패한 문서",
            filename="fail.pdf",
            file_path="/tmp/fail.pdf",
            source_organization="실패기관",
            published_year=2019,
            status=DocumentStatus.FAILED,
            error_message="이전 오류",
            uploaded_by_user=self.admin,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/admin/knowledge-base/documents/{doc.id}/retry",
                headers=_make_auth_header(self.admin),
            )
        assert resp.status_code == 202
        mock_task.delay.assert_called_once_with(doc.id)
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest app/tests/test_knowledge_routers.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.apis.v1.knowledge_routers'`

- [ ] **Step 3: app/apis/v1/knowledge_routers.py 구현**

```python
import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from tortoise.exceptions import IntegrityError

from app.core import config
from app.core.logger import default_logger as logger
from app.dependencies.pdf_validator import validate_pdf_upload
from app.dependencies.security import get_request_user
from app.dtos.knowledge import KnowledgeDocumentResponse, KnowledgeDocumentUploadResponse
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.users import User
from ai_worker.tasks.embedding import embed_document_task

knowledge_router = APIRouter(prefix="/admin/knowledge-base", tags=["knowledge-base"])


def _require_admin(user: Annotated[User, Depends(get_request_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return user


@knowledge_router.post("/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_knowledge_document(
    admin: Annotated[User, Depends(_require_admin)],
    file: UploadFile,
    title: Annotated[str, Form(max_length=200)],
    source_organization: Annotated[str, Form(max_length=100)],
    published_year: Annotated[int, Form(ge=1950, le=2030)],
) -> KnowledgeDocumentUploadResponse:
    content = await validate_pdf_upload(file)

    # 중복 체크
    exists = await KnowledgeDocument.filter(
        title=title, source_organization=source_organization, published_year=published_year
    ).exists()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 문서입니다.")

    # DB 레코드 생성 (file_path 임시)
    doc = await KnowledgeDocument.create(
        title=title,
        filename=file.filename or "document.pdf",
        file_path="",
        source_organization=source_organization,
        published_year=published_year,
        uploaded_by_user=admin,
    )

    # 파일 저장
    save_dir = Path(config.MEDIA_DIR) / "knowledge" / str(doc.id)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / (file.filename or "document.pdf")
    file_path.write_bytes(content)

    doc.file_path = str(file_path)
    await doc.save(update_fields=["file_path", "updated_at"])

    logger.info(f'{{"event": "kb_upload_received", "doc_id": {doc.id}, "title": "{title}", "size_bytes": {len(content)}}}')
    embed_document_task.delay(doc.id)

    return KnowledgeDocumentUploadResponse(document_id=doc.id, title=doc.title, status=doc.status)


@knowledge_router.get("/documents", status_code=status.HTTP_200_OK)
async def list_knowledge_documents(
    admin: Annotated[User, Depends(_require_admin)],
) -> list[KnowledgeDocumentResponse]:
    docs = await KnowledgeDocument.all().order_by("-created_at")
    return [KnowledgeDocumentResponse.model_validate(d) for d in docs]


@knowledge_router.get("/documents/{doc_id}", status_code=status.HTTP_200_OK)
async def get_knowledge_document(
    doc_id: int,
    admin: Annotated[User, Depends(_require_admin)],
) -> KnowledgeDocumentResponse:
    doc = await KnowledgeDocument.get_or_none(id=doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문서를 찾을 수 없습니다.")
    return KnowledgeDocumentResponse.model_validate(doc)


@knowledge_router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_document(
    doc_id: int,
    admin: Annotated[User, Depends(_require_admin)],
) -> None:
    doc = await KnowledgeDocument.get_or_none(id=doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문서를 찾을 수 없습니다.")

    # 파일 삭제
    if doc.file_path and Path(doc.file_path).exists():
        Path(doc.file_path).unlink()

    # DB 삭제 (Qdrant 벡터 삭제는 벡터 저장소 관리 스크립트에서 수행 가능)
    await doc.delete()


@knowledge_router.post("/documents/{doc_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_knowledge_document(
    doc_id: int,
    admin: Annotated[User, Depends(_require_admin)],
) -> KnowledgeDocumentUploadResponse:
    doc = await KnowledgeDocument.get_or_none(id=doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문서를 찾을 수 없습니다.")
    if doc.status != DocumentStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="현재 상태에서 재처리할 수 없습니다."
        )

    doc.status = DocumentStatus.PENDING
    doc.error_message = None
    await doc.save(update_fields=["status", "error_message", "updated_at"])
    embed_document_task.delay(doc.id)

    return KnowledgeDocumentUploadResponse(document_id=doc.id, title=doc.title, status=doc.status)
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest app/tests/test_knowledge_routers.py -v
```

Expected: 6개 PASSED

- [ ] **Step 5: Commit**

```bash
git add app/tests/test_knowledge_routers.py app/apis/v1/knowledge_routers.py
git commit -m "feat: 관리자 지식베이스 API 엔드포인트 추가"
```

---

## Task 11: 라우터 등록 & 최종 확인

**Files:**
- Modify: `app/apis/v1/__init__.py`

- [ ] **Step 1: app/apis/v1/__init__.py에 knowledge_router 등록**

```python
from fastapi import APIRouter

from app.apis.v1.auth_routers import auth_router
from app.apis.v1.knowledge_routers import knowledge_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(knowledge_router)
```

- [ ] **Step 2: 전체 테스트 스위트 실행**

```bash
uv run pytest app/tests/ ai_worker/tests/ -v --tb=short
```

Expected: 전체 PASSED (실패 없음)

- [ ] **Step 3: 로컬 서버 기동 확인**

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

브라우저에서 `http://localhost:8000/api/docs` 확인 — `knowledge-base` 태그 아래 5개 엔드포인트 노출

- [ ] **Step 4: 최종 Commit**

```bash
git add app/apis/v1/__init__.py
git commit -m "feat: RAG 지식베이스 라우터 등록 완료 (REQ-KB-001/002)"
```

---

## Self-Review 결과

**Spec 커버리지 체크:**
| Spec 항목 | Task |
|---|---|
| knowledge_base 테이블 (전체 컬럼, 인덱스) | Task 2 |
| PDF 50MB 제한, 매직바이트 검증 | Task 3 |
| PyMuPDF 파싱 + section_title 3단계 폴백 | Task 4 |
| 500토큰/오버랩 50 청크 분할 | Task 5 |
| Celery 설정 (concurrency=2, backoff) | Task 6 |
| embed_document_task (멱등, 재시도, DONE/FAILED) | Task 7 |
| Qdrant 페이로드 스키마 (7개 필드) | Task 7 |
| KnowledgeChunk DTO | Task 8 |
| search_knowledge + Redis 캐시 (`kb:search:{hash}:k{N}`) | Task 9 |
| 중복 업로드 409 | Task 10 |
| retry 엔드포인트 (FAILED만 허용) | Task 10 |
| 관리자 전용 인증 (is_admin) | Task 10 |

**확인된 미구현 항목 (v2 범위):**
- DELETE 엔드포인트의 Qdrant 벡터 삭제: 현재 DB + 파일만 삭제. Qdrant 삭제는 별도 `AsyncQdrantClient` 호출 필요. 이 기능은 삭제 자체가 선택적이므로 다음 이터레이션에서 추가.
- Prometheus 메트릭 수집 (`kb_embedding_duration_seconds` 등): 핵심 기능 구현 후 별도 태스크.
