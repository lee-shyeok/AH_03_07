# RAG 지식베이스 설계 (REQ-KB-001 / REQ-KB-002)

**날짜:** 2026-05-18  
**담당자:** 허승혜  
**관련 요구사항:** REQ-KB-001 (초기 임베딩), REQ-KB-002 (유사도 검색)  
**연동 요구사항:** REQ-KB-003 (출처 표시), REQ-CHAT-007 (자가면역 챗봇), REQ-AUTO-005 (맞춤 안내문)

---

## 1. 목적

자가면역 모드(루푸스, 류마티스관절염 등) 챗봇과 안내문 생성에 사용되는  
임상 가이드라인 지식베이스를 구축하고, 유사도 기반 검색을 제공한다.

**수집 대상 문서:**
- 대한류마티스학회 진료지침
- EULAR 권고안 (요약/공개 자료)
- ACR 가이드라인 (요약/공개 자료)
- 식약처 자가면역 약물 의약품 정보

---

## 2. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│  관리자 (is_admin=True)                                  │
└────────────────┬────────────────────────────────────────┘
                 │ POST /api/v1/admin/knowledge-base/documents
                 │ (multipart/form-data, max 50MB)
                 ▼
┌────────────────────────────────────────────────────────┐
│  FastAPI (app/)                                        │
│  • Magic number / MIME 검증 → 400                      │
│  • 중복 체크 (title+org+year UNIQUE) → 409             │
│  • PDF 저장 (media/knowledge/{id}/)                    │
│  • knowledge_base 레코드 생성 (status=PENDING)        │
│  • embed_document_task.delay(doc_id) → Redis           │
│  • 202 Accepted 즉시 반환                              │
│                                                        │
│  내부 소비자:                                           │
│  • 챗봇 서비스 (REQ-CHAT-007)   ─┐                    │
│  • 안내문 서비스 (REQ-AUTO-005) ─┤→ search_knowledge() │
└────────┬─────────────────────────┴───────────────────┬─┘
         │                                             │
         ▼                                             ▼
┌──────────────────┐                      ┌────────────────────┐
│  Redis           │                      │  Qdrant            │
│  • Celery Broker │                      │  collection:       │
│  • Celery Result │                      │  medical_kb        │
│  • 검색 캐시     │                      │  vector_size: 1536 │
│    (TTL 24h)     │                      │  distance: Cosine  │
└────────┬─────────┘                      └────────────────────┘
         │ task queue                              ▲
         ▼                                         │ upsert
┌────────────────────────────────────────────────────────┐
│  ai_worker (Celery Worker, concurrency=2)              │
│  embed_document_task(doc_id):                          │
│    1. DB에서 knowledge_base 레코드 조회                │
│    2. 기존 Qdrant 포인트 삭제 (재처리 멱등성)          │
│    3. PyMuPDF로 PDF 텍스트 + section_title 추출        │
│    4. 500토큰/오버랩 50토큰 청크 분할                  │
│    5. OpenAI text-embedding-3-small (batch 100청크)    │
│    6. Qdrant upsert (payload 포함)                     │
│    7. DB status → DONE / FAILED                        │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│  MySQL — knowledge_base 테이블                         │
└────────────────────────────────────────────────────────┘
```

---

## 3. 컴포넌트 상세

### 3-1. MySQL 테이블: `knowledge_base`

**컬럼 정의:**

| 컬럼명 | 타입 | NULL | 설명 |
|---|---|---|---|
| `id` | BIGINT PK AUTO_INCREMENT | NOT NULL | — |
| `title` | VARCHAR(200) | NOT NULL | 문서 제목 (예: "EULAR 2022 RA 권고안") |
| `filename` | VARCHAR(255) | NOT NULL | 원본 파일명 |
| `file_path` | VARCHAR(500) | NOT NULL | 서버 내 파일 경로 (media/knowledge/{id}/) |
| `status` | ENUM('PENDING','PROCESSING','DONE','FAILED') | NOT NULL | 처리 상태 |
| `chunk_count` | INT | NULL | 생성된 청크 수 (DONE 후 기록) |
| `source_organization` | VARCHAR(100) | NOT NULL | 발간 기관 (예: "EULAR", "대한류마티스학회") |
| `published_year` | SMALLINT | NOT NULL | 발간 연도 (1950–2030) |
| `error_message` | TEXT | NULL | FAILED 시 오류 내용 |
| `uploaded_by_user_id` | BIGINT FK → users.id | NOT NULL | 업로드한 관리자 |
| `created_at` | DATETIME | NOT NULL | 생성 일시 (auto) |
| `updated_at` | DATETIME | NOT NULL | 최근 수정 일시 (auto) |

**인덱스:**

| 인덱스명 | 컬럼 | 종류 | 목적 |
|---|---|---|---|
| `idx_status` | `status` | 일반 | 상태별 문서 목록 조회 |
| `idx_uploaded_by` | `uploaded_by_user_id` | 일반 | 담당자별 문서 조회 |
| `idx_created_at` | `created_at DESC` | 일반 | 최신순 정렬 |
| `uq_document` | `(title, source_organization, published_year)` | UNIQUE | 중복 업로드 방지 |

**문서 상태 전이:**
```
PENDING → PROCESSING → DONE
                     ↘ FAILED → (retry) → PROCESSING → DONE
```

### 3-2. Qdrant 벡터 페이로드 스키마

각 청크가 Qdrant에 저장될 때의 포인트 구조:

```json
{
  "id": "<uuid-v5(doc_id, chunk_index)>",
  "vector": [0.012, -0.034, ...],
  "payload": {
    "document_id": 42,
    "chunk_index": 7,
    "page_number": 15,
    "section_title": "류마티스관절염 약물 치료 지침",
    "source_title": "EULAR 2022 RA 권고안",
    "source_organization": "EULAR",
    "published_year": 2022,
    "text": "메토트렉세이트는 RA 초치료의 기본 약물로 권고된다..."
  }
}
```

> **포인트 ID:** `uuid.uuid5(NAMESPACE_DNS, f"{doc_id}:{chunk_index}")` — 결정론적 ID로  
> 재처리 시 동일 doc_id의 기존 벡터를 Qdrant `delete(filter={"document_id": doc_id})`로  
> 삭제한 뒤 upsert하여 중복 없이 멱등 처리한다.  
> `section_title`, `source_title`, `source_organization`은 REQ-KB-003 출처 표시에 직접 사용된다.  
> `section_title`이 추출 불가한 경우 `null` 허용.

**Qdrant 컬렉션 초기화:**  
ai_worker 시작 시 `medical_kb` 컬렉션이 없으면 자동 생성한다.

```python
# ai_worker/core/qdrant_init.py
if not client.collection_exists("medical_kb"):
    client.create_collection(
        collection_name="medical_kb",
        vectors_config=VectorsConfig(size=1536, distance=Distance.COSINE),
    )
```

### 3-3. Celery 태스크: `embed_document_task`

**위치:** `ai_worker/tasks/embedding.py`

```
embed_document_task(doc_id: int)
  ├── max_retries = 3
  ├── autoretry_for = (OpenAIError, QdrantException, IOError, ConnectionError)
  ├── retry_backoff = True (지수 백오프, 최대 300초)
  └── 처리 순서:
       1. knowledge_base.status → PROCESSING
       2. 기존 Qdrant 포인트 삭제 (filter: document_id == doc_id)
          → 재처리 멱등성 보장
       3. PyMuPDF로 PDF 텍스트 추출 (블록 단위, 레이아웃 보존)
          └── /JavaScript, /JS 액션 포함 시 즉시 FAILED
       4. section_title 추출 (청크별, 3단계 폴백):
          ├── 1차: 폰트 크기 기반 헤더 감지
          │        (블록 내 최대 폰트 크기 ≥ 페이지 평균 폰트 크기 * 1.2)
          ├── 2차: 정규식 패턴 매칭
          │        (^제\s*\d+\s*장, ^\d+\.\d+\s, ^[IVX]+\.\s)
          ├── 3차: 직전 청크의 section_title 상속
          └── 폴백: null
       5. RecursiveCharacterTextSplitter
          (500토큰, 오버랩 50토큰, tiktoken cl100k_base 인코딩 기준)
       6. OpenAI text-embedding-3-small
          (batch 처리: 최대 100청크/요청, rate limit 준수)
       7. Qdrant upsert (포인트 ID = uuid5(doc_id, chunk_index))
       8. knowledge_base.chunk_count 업데이트, status → DONE
       실패 시: status → FAILED, error_message 기록
```

**동시성 정책:**  
`worker concurrency = 2`  
OpenAI text-embedding-3-small Tier 1 기준 3,000 RPM / 1,000,000 TPM.  
문서 1개당 최대 약 200청크 × 배치 2개 = 2 RPM. 동시 작업자 2개 시 최대 4 RPM.  
단일 문서(~10만 토큰) 처리 시 TPM 한도 내 안전.

### 3-4. 검색 서비스: `search_knowledge(query, top_k=5)`

**위치:** `app/services/knowledge_search.py`

```
search_knowledge(query: str, top_k: int = 5) → list[KnowledgeChunk]
  1. cache_key = f"kb:search:{sha256(query.strip().lower())}:k{top_k}"
  2. Redis 캐시 조회 (TTL 86400초 = 24h)
  3. 캐시 HIT  → 즉시 반환
  4. 캐시 MISS:
     a. OpenAI text-embedding-3-small로 query 임베딩
     b. Qdrant cosine similarity search, top_k=top_k
     c. 결과를 Redis에 직렬화(JSON) 후 캐싱 (TTL 86400초)
     d. 반환
  5. Redis 장애 시 → 캐시 건너뛰고 Qdrant 직접 검색 (폴백)
```

> 캐시 키에 `top_k`를 포함하여 `top_k=5`와 `top_k=10` 결과가 섞이지 않도록 한다.  
> 로깅 시 원본 query는 기록하지 않고 SHA256 해시만 기록한다 (PII 보호).

반환 타입 `KnowledgeChunk` (`app/dtos/knowledge.py`):
```python
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
```

### 3-5. 관리자 API 엔드포인트

> **참고:** REQ-KB-001/002는 내부 인프라 요구사항으로, 명세서에 공개 API가 정의되어 있지 않다.  
> 아래는 관리자 문서 관리를 위한 엔드포인트이며 모두 `is_admin=True` 인증을 요구한다.

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/v1/admin/knowledge-base/documents` | PDF 업로드 + 임베딩 큐 등록 |
| GET | `/api/v1/admin/knowledge-base/documents` | 문서 목록 조회 |
| GET | `/api/v1/admin/knowledge-base/documents/{id}` | 문서 상태 조회 |
| DELETE | `/api/v1/admin/knowledge-base/documents/{id}` | 문서 삭제 (DB + Qdrant + 파일 시스템) |
| POST | `/api/v1/admin/knowledge-base/documents/{id}/retry` | 실패 문서 재처리 |

---

**POST `/api/v1/admin/knowledge-base/documents`**

요청: `multipart/form-data`

```python
class KnowledgeDocumentCreateForm:
    file: UploadFile                          # PDF 파일, max 50MB
    title: str = Form(..., max_length=200)
    source_organization: str = Form(..., max_length=100)
    published_year: int = Form(..., ge=1950, le=2030)
```

Pydantic 검증 규칙:
- `file`: Content-Type `application/pdf` + Magic number `%PDF-` 검증, 50MB 초과 시 413
- `title`: 공백 제거 후 길이 1–200
- `source_organization`: 공백 제거 후 길이 1–100
- `published_year`: 1950 이상, 2030 이하

응답:

| 코드 | 조건 |
|---|---|
| 202 | 정상 접수 |
| 400 | PDF 검증 실패 (잘못된 형식, 악성 콘텐츠) |
| 409 | `(title, source_organization, published_year)` 조합 중복 |
| 413 | 파일 크기 50MB 초과 |

```json
// 202 Accepted
{
  "document_id": 42,
  "title": "EULAR 2022 RA 권고안",
  "status": "PENDING"
}
```

---

**POST `/api/v1/admin/knowledge-base/documents/{id}/retry`**

FAILED 상태의 문서를 재처리 큐에 등록한다.

| 코드 | 조건 |
|---|---|
| 202 | 정상 재큐잉 |
| 404 | 문서 없음 |
| 409 | 현재 상태가 FAILED가 아님 (PENDING / PROCESSING / DONE) |

```json
// 202 Accepted
{
  "document_id": 42,
  "status": "PENDING"
}
```

재처리 흐름: status → PENDING → `embed_document_task.delay(doc_id)` → 202 반환.  
Celery 태스크 시작 시 기존 Qdrant 포인트 삭제 후 재임베딩 (멱등 처리).

---

## 4. PDF 파일 검증

업로드 수신 즉시 FastAPI에서 3단계 검증을 수행한다.

| 단계 | 검증 항목 | 실패 응답 |
|---|---|---|
| 1 | 파일 크기 ≤ 50MB | 413 |
| 2 | Magic number `%PDF-` (파일 앞 5바이트) | 400 |
| 3 | MIME type `application/pdf` (python-magic 또는 Content-Type 헤더) | 400 |

Celery 태스크에서 추가 검증 (PyMuPDF 파싱 단계):

| 검증 항목 | 실패 처리 |
|---|---|
| `/JavaScript`, `/JS` 액션 포함 여부 | status=FAILED, "악성 콘텐츠 감지" |
| PyMuPDF 파싱 예외 | status=FAILED, "PDF 파싱 실패: {상세}" |

---

## 5. 청크 크기 결정 근거

**결정: 500토큰 / 오버랩 50토큰** (요구사항 명세서 명시, tiktoken cl100k_base 기준)

| 설정 | 토큰 수 | 장점 | 단점 |
|---|---|---|---|
| Small | 300 | 정밀한 매칭 | 임상 문장이 잘림, 문맥 손실 |
| **채택** | **500** | **임상 단락 1–2개 포함, 균형점** | — |
| Large | 700 | 긴 문맥 보존 | 관련 없는 내용 혼입 위험 |

의료 가이드라인은 단락 단위로 의미가 완결된다 (권고 등급 + 근거 + 주의사항이 한 단락).  
500토큰은 이 패턴에 자연스럽게 들어맞으며, top-k=5 검색 시 총 2,500토큰이 LLM 컨텍스트에 주입된다.

---

## 6. PDF 파서 선택 근거

**결정: PyMuPDF (fitz)**

| | pypdf | PyMuPDF (fitz) |
|---|---|---|
| 테이블 추출 | 미지원 (텍스트 흐름만) | 지원 (행·열 구조 보존) |
| 한글 처리 | 보통 | 우수 |
| 복잡한 레이아웃 | 열 순서 뒤섞임 위험 | 레이아웃 보존 |
| 폰트 크기 메타데이터 | 미제공 | 제공 (section_title 추출에 활용) |
| 처리 속도 | 빠름 | 더 빠름 |
| 패키지 크기 | ~500KB | ~15MB |

의료 PDF에는 약물 용량 표·권고 등급 표가 많고, section_title 추출에 폰트 크기 정보가 필요하므로 PyMuPDF가 필수적이다.

---

## 7. 오류 처리

| 상황 | 처리 방식 |
|---|---|
| 파일 크기 > 50MB | 413 Request Entity Too Large |
| Magic number / MIME 불일치 | 400 Bad Request: "PDF 검증 실패: 잘못된 파일 형식" |
| 중복 업로드 | 409 Conflict: "이미 등록된 문서입니다" |
| FAILED 아닌 문서에 retry | 409 Conflict: "현재 상태에서 재처리할 수 없습니다" |
| PDF에 JavaScript 액션 감지 | status=FAILED, error_message: "PDF 검증 실패: 악성 콘텐츠 감지" |
| PDF 파싱 불가 | status=FAILED, error_message: "PDF 파싱 실패: {상세}" |
| OpenAI API 오류 | 지수 백오프, 최대 3회 재시도 |
| Qdrant 연결 실패 | 동일 재시도 정책 |
| 3회 재시도 모두 실패 | status=FAILED, error_message 기록, retry 엔드포인트로 재처리 가능 |
| Redis 장애 (검색 캐시) | 캐시 없이 Qdrant 직접 검색 (폴백) |

---

## 8. 로깅 정책

구조화 로깅 (JSON 포맷, `ai_worker/core/logger.py` 기반 확장).

**FastAPI — 업로드 엔드포인트:**
```json
{"event": "kb_upload_received",  "doc_id": 42, "title": "...", "size_bytes": 1234567}
{"event": "kb_upload_duplicate", "title": "...", "org": "EULAR", "year": 2022}
{"event": "kb_pdf_invalid",      "doc_id": 42, "reason": "악성 콘텐츠 감지"}
```

**ai_worker — Celery 태스크:**
```json
{"event": "embed_task_start",    "doc_id": 42, "task_id": "..."}
{"event": "embed_task_done",     "doc_id": 42, "chunk_count": 187, "duration_sec": 43.2}
{"event": "embed_task_failed",   "doc_id": 42, "error": "...", "retry": 1}
```

**검색 서비스 — query는 SHA256 해시만 기록 (PII 보호):**
```json
{"event": "kb_search_hit",  "query_hash": "a3f4...", "top_k": 5}
{"event": "kb_search_miss", "query_hash": "a3f4...", "top_k": 5, "duration_ms": 120}
```

---

## 9. 메트릭

Prometheus 형식으로 수집 (`/metrics` 엔드포인트 또는 Celery 시그널).

| 메트릭 이름 | 종류 | 레이블 | 설명 |
|---|---|---|---|
| `kb_embedding_duration_seconds` | Histogram | `status` | 문서 1건 임베딩 총 소요 시간 |
| `kb_search_cache_hit_total` | Counter | — | 검색 캐시 HIT 횟수 |
| `kb_search_cache_miss_total` | Counter | — | 검색 캐시 MISS 횟수 |
| `kb_documents_by_status` | Gauge | `status` | 상태별 문서 수 |
| `kb_celery_retry_total` | Counter | — | Celery 태스크 재시도 횟수 (doc_id는 고카디널리티로 레이블 제외) |

---

## 10. 테스트 전략

| 테스트 | 대상 | 방법 |
|---|---|---|
| 청크 분할 | `chunk_text()` 함수 | 단위 테스트: 경계값(0토큰, 정확히 500토큰, 501토큰, 오버랩 검증) |
| section_title 추출 | `extract_section_title()` | 단위 테스트: 폰트 크기 케이스 / 정규식 매칭 케이스 / 상속 케이스 / null 케이스 |
| PDF 검증 | `validate_pdf()` | 단위 테스트: 정상 PDF / 잘못된 Magic number / JavaScript 포함 PDF |
| 업로드 API | `POST /admin/knowledge-base/documents` | Tortoise TestCase: 정상 업로드(202) / 중복(409) / 50MB 초과(413) / 잘못된 PDF(400) |
| 재처리 API | `POST .../retry` | Tortoise TestCase: FAILED→202 / DONE→409 |
| 임베딩 태스크 | `embed_document_task` | Celery eager 모드, OpenAI + Qdrant mock, 멱등성 검증 (2회 실행 후 벡터 수 동일) |
| 검색 서비스 | `search_knowledge()` | 통합 테스트: Redis mock + Qdrant mock, 캐시 HIT/MISS 분기 + 캐시 키 top_k 분리 검증 |

---

## 11. 추가 의존성

`pyproject.toml`:

```toml
[dependency-groups]
app = [
    # ... 기존 항목들 ...
    "celery[redis]>=5.4.0,<6.0.0",
    "openai>=1.30.0,<2.0.0",
    "qdrant-client>=1.12.0,<2.0.0",
]
ai = [
    # ... 기존 항목들 ...
    "celery[redis]>=5.4.0,<6.0.0",
    "pymupdf>=1.24.0,<2.0.0",
    "openai>=1.30.0,<2.0.0",
    "qdrant-client>=1.12.0,<2.0.0",
    "tiktoken>=0.7.0,<1.0.0",
]
```

`docker-compose.yml`에 Qdrant 서비스 추가:

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

`ai-worker` 서비스에 Qdrant 의존성 추가:
```yaml
ai-worker:
  depends_on:
    mysql:
      condition: service_healthy
    redis:
      condition: service_healthy
    qdrant:
      condition: service_healthy
```

환경 변수 (`envs/example.local.env`에 추가):
```
OPENAI_API_KEY=sk-...
QDRANT_HOST=qdrant
QDRANT_PORT=6333
CELERY_WORKER_CONCURRENCY=2
```

---

## 12. 벡터 스토어 선택 참고

> **명세서 기술 참고에는 pgvector가 명시되어 있으나**, pgvector는 PostgreSQL 전용 확장이며  
> 현재 인프라는 MySQL 8.0 기반이다. MySQL 8.0은 벡터 연산을 지원하지 않으므로  
> pgvector를 그대로 적용할 수 없다.  
> Qdrant는 pgvector와 동일한 벡터 유사도 검색 기능을 독립 서비스로 제공하며,  
> 기존 MySQL 인프라 변경 없이 사용 가능하다.
