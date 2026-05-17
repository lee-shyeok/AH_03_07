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
                 ▼
┌────────────────────────────────────────────────────────┐
│  FastAPI (app/)                                        │
│  • PDF 수신 + 파일 저장 (media/knowledge/)             │
│  • DB에 knowledge_base 레코드 생성 (status=PENDING)   │
│  • Celery 태스크 큐에 embed_document_task(doc_id)      │
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
│  ai_worker (Celery Worker)                             │
│  embed_document_task(doc_id):                          │
│    1. DB에서 knowledge_base 레코드 조회                │
│    2. 파일 시스템에서 PDF 읽기                          │
│    3. PyMuPDF로 텍스트 추출 (레이아웃 보존)            │
│    4. 500토큰/오버랩 50토큰 청크 분할                  │
│    5. OpenAI text-embedding-3-small 호출               │
│    6. Qdrant에 벡터 + 페이로드 upsert                 │
│    7. DB status → DONE (또는 FAILED + error_message)  │
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

| 컬럼명 | 타입 | 설명 |
|---|---|---|
| `id` | BIGINT PK | 자동 증가 |
| `title` | VARCHAR(200) | 문서 제목 (예: "EULAR 2022 RA 권고안") |
| `filename` | VARCHAR(255) | 원본 파일명 |
| `file_path` | VARCHAR(500) | 서버 내 파일 경로 (media/knowledge/{id}/) |
| `status` | ENUM | PENDING / PROCESSING / DONE / FAILED |
| `chunk_count` | INT | 생성된 청크 수 (완료 후 기록) |
| `source_organization` | VARCHAR(100) | 발간 기관 (예: "EULAR", "대한류마티스학회") |
| `published_year` | SMALLINT | 발간 연도 |
| `error_message` | TEXT NULL | FAILED 시 오류 내용 |
| `uploaded_by_user_id` | BIGINT FK → users.id | 업로드한 관리자 |
| `created_at` | DATETIME | 생성 일시 |
| `updated_at` | DATETIME | 최근 수정 일시 |

**문서 상태 전이:**
```
PENDING → PROCESSING → DONE
                     ↘ FAILED
```

### 3-2. Qdrant 벡터 페이로드 스키마

각 청크가 Qdrant에 저장될 때 포함되는 메타데이터:

```json
{
  "document_id": 42,
  "chunk_index": 7,
  "page_number": 15,
  "section_title": "류마티스관절염 약물 치료 지침",
  "source_title": "EULAR 2022 RA 권고안",
  "source_organization": "EULAR",
  "published_year": 2022,
  "text": "메토트렉세이트는 RA 초치료의 기본 약물로 권고된다..."
}
```

> `section_title`, `source_title`, `source_organization`은 REQ-KB-003 출처 표시에 직접 사용된다.

### 3-3. Celery 태스크: `embed_document_task`

**위치:** `ai_worker/tasks/embedding.py`

```
embed_document_task(doc_id: int)
  ├── max_retries = 3
  ├── autoretry_for = (OpenAIError, QdrantException)
  ├── retry_backoff = True (지수 백오프)
  └── 처리 순서:
       1. knowledge_base.status → PROCESSING
       2. PyMuPDF로 PDF 텍스트 추출
       3. RecursiveCharacterTextSplitter (500토큰, 오버랩 50토큰, tiktoken cl100k_base 인코딩 기준)
       4. OpenAI text-embedding-3-small (batch 처리, 최대 100청크/요청)
       5. Qdrant upsert (collection: medical_kb, vector_size: 1536)
       6. knowledge_base.chunk_count 업데이트, status → DONE
       실패 시: status → FAILED, error_message 기록
```

### 3-4. 검색 서비스: `search_knowledge(query, top_k=5)`

**위치:** `app/services/knowledge_search.py`

```
search_knowledge(query: str, top_k: int = 5) → list[KnowledgeChunk]
  1. Redis 캐시 조회 (key: "kb:search:{sha256(query)}", TTL 24h)
  2. 캐시 HIT → 즉시 반환
  3. 캐시 MISS:
     a. OpenAI text-embedding-3-small로 query 임베딩
     b. Qdrant cosine similarity search, top_k=5
     c. 결과를 Redis에 캐싱 (TTL 86400초)
     d. 반환
```

반환 타입 `KnowledgeChunk`:
```python
@dataclass
class KnowledgeChunk:
    document_id: int
    chunk_index: int
    text: str
    score: float         # 유사도 점수
    page_number: int
    section_title: str
    source_title: str
    source_organization: str
    published_year: int
```

### 3-5. 관리자 API 엔드포인트

> **참고:** REQ-KB-001/002는 내부 인프라 요구사항으로, 명세서에 공개 API가 정의되어 있지 않다.  
> 아래는 관리자 문서 관리를 위한 내부 엔드포인트이다.

| Method | Path | 설명 | Auth |
|---|---|---|---|
| POST | `/api/v1/admin/knowledge-base/documents` | PDF 업로드 + 임베딩 큐 등록 | is_admin |
| GET | `/api/v1/admin/knowledge-base/documents` | 문서 목록 조회 | is_admin |
| GET | `/api/v1/admin/knowledge-base/documents/{id}` | 문서 상태 조회 (처리 진행률 포함) | is_admin |
| DELETE | `/api/v1/admin/knowledge-base/documents/{id}` | 문서 삭제 (DB + Qdrant 벡터 + 파일 시스템 삭제) | is_admin |

**POST 응답 (202 Accepted):**
```json
{
  "document_id": 42,
  "title": "EULAR 2022 RA 권고안",
  "status": "PENDING"
}
```

---

## 4. 청크 크기 결정 근거

**결정: 500토큰 / 오버랩 50토큰** (요구사항 명세서 명시)

| 설정 | 토큰 수 | 장점 | 단점 |
|---|---|---|---|
| Small | 300 | 정밀한 매칭 | 임상 문장이 잘림, 문맥 손실 |
| **채택** | **500** | **임상 단락 1-2개 포함, 균형점** | — |
| Large | 700 | 긴 문맥 보존 | 관련 없는 내용 혼입 위험 |

의료 가이드라인은 단락 단위로 의미가 완결된다 (권고 등급 + 근거 + 주의사항이 한 단락).  
500토큰은 이 패턴에 자연스럽게 들어맞으며, top-k=5 검색 시 총 2500토큰이 LLM 컨텍스트에 주입된다.

---

## 5. PDF 파서 선택 근거

**결정: PyMuPDF (fitz)**

| | pypdf | PyMuPDF (fitz) |
|---|---|---|
| 테이블 추출 | 미지원 (텍스트 흐름만) | 지원 (행·열 구조 보존) |
| 한글 처리 | 보통 | 우수 |
| 복잡한 레이아웃 | 열 순서 뒤섞임 위험 | 레이아웃 보존 |
| 처리 속도 | 빠름 | 더 빠름 |
| 패키지 크기 | ~500KB | ~15MB |

의료 PDF에는 약물 용량 표, 권고 등급 표가 많다. pypdf는 이런 레이아웃을 단순 텍스트 흐름으로 처리해 행·열 순서가 뒤섞일 수 있다.  
PyMuPDF는 블록 단위로 텍스트를 추출하여 표 구조를 보존하므로 의료 문서에 적합하다.

---

## 6. 오류 처리

| 상황 | 처리 방식 |
|---|---|
| OpenAI API 오류 | 지수 백오프 + 최대 3회 재시도 |
| Qdrant 연결 실패 | 동일 재시도 정책 |
| PDF 파싱 불가 | FAILED + error_message: "PDF 파싱 실패: {상세}" |
| 3회 재시도 모두 실패 | status=FAILED, error_message 기록, 관리자 재처리 가능 |
| 검색 캐시 오류 | Redis 장애 시 캐시 없이 Qdrant 직접 검색 (폴백) |

---

## 7. 테스트 전략

| 테스트 | 대상 | 방법 |
|---|---|---|
| 청크 분할 | `chunk_text()` 함수 | 단위 테스트: 경계값(0토큰, 정확히 500토큰, 501토큰) |
| 임베딩 태스크 | `embed_document_task` | 통합 테스트: Celery 태스크를 eager 모드로 실행, OpenAI·Qdrant mock |
| 업로드 API | `POST /admin/knowledge-base/documents` | Tortoise TestCase: 파일 업로드 + DB 상태 PENDING 확인, Celery task mock |
| 검색 API | `search_knowledge()` | 통합 테스트: Redis mock + Qdrant mock, 캐시 HIT/MISS 분기 검증 |

---

## 8. 추가 의존성

`pyproject.toml`의 `[dependency-groups]`에 추가:

```toml
[dependency-groups]
app = [
    # ... 기존 항목들 ...
    "celery[redis]>=5.4.0",
    "openai>=1.84.0",
    "qdrant-client>=1.14.0",
]
ai = [
    # ... 기존 항목들 ...
    "celery[redis]>=5.4.0",
    "pymupdf>=1.25.0",
    "openai>=1.84.0",
    "qdrant-client>=1.14.0",
    "tiktoken>=0.9.0",
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
```

---

## 9. 벡터 스토어 선택 참고

> **명세서 기술 참고에는 pgvector가 명시되어 있으나**, pgvector는 PostgreSQL 전용 확장이며  
> 현재 인프라는 MySQL 8.0 기반이다. MySQL 8.0은 벡터 연산을 지원하지 않으므로  
> pgvector를 그대로 적용할 수 없다.  
> Qdrant는 pgvector와 동일한 벡터 유사도 검색 기능을 독립 서비스로 제공하며,  
> 기존 MySQL 인프라 변경 없이 사용 가능하다.
