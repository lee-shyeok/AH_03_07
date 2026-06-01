# REQ-CHAT-002 설계 문서

**날짜:** 2026-06-02  
**담당자:** 권순현 (tnsgus375)  
**브랜치:** feature/req-chat-002  

---

## 1. 요구사항 요약

사용자가 챗봇에 질문을 보내면 **SSE 스트리밍** 방식으로 실시간 응답을 받는다.

- LLM: GPT-4o-mini, Temperature 0.7
- 컨텍스트: 최근 10턴 대화 히스토리 + 사용자 프로필(mode + 등록 질환) + 최근 30일 가이드
- 처리 시간 목표: 첫 토큰 1.5초 이내, 전체 5초 이내
- 스트리밍 방식: SSE (text/event-stream)

---

## 2. 파일 구조

### 신규 파일 (권순현 전담)

```
app/
├── apis/v1/
│   └── chat_stream_routers.py   # 엔드포인트 1개, 인증/세션 검증
├── services/
│   └── chat_stream_service.py   # SSE 생성기, LLM 호출, DB 저장
└── dtos/
    └── chat_stream.py           # StreamMessageRequest DTO
```

### 수정 파일 (1줄 추가)

```
app/apis/v1/__init__.py          # chat_stream_router 등록
```

### 절대 수정 금지 (허승혜 작업)

- `chat_routers.py`
- `chat_message_service.py`, `chat_session_service.py`, `chat_rag_service.py`
- `chat_message.py`, `chat_session.py` (모델)
- `app/dtos/chat.py`
- `chat_validation_service.py` (import만 허용)

---

## 3. 엔드포인트 스펙

```
POST /api/v1/chat/sessions/{session_id}/messages/stream

Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json
  Accept: text/event-stream

Path Parameters:
  session_id: int

Request Body:
  {"message": "메트포르민 식전 복용해도 되나요?"}
  - message: 1자 이상, 4000자 이하

Response:
  Content-Type: text/event-stream
  Transfer-Encoding: chunked
```

### HTTP 에러 코드 (스트리밍 전 체크)

| 코드 | 조건 |
|------|------|
| 401 | 인증 실패 |
| 404 | 세션 없음 (또는 본인 세션 아님) |
| 410 | 세션 생성 후 30분 초과 |
| 422 | message 빈값 or 4000자 초과 |

---

## 4. SSE 이벤트 타입

모든 이벤트는 `data: {JSON}\n\n` 형식.

```
# 정상 토큰 스트리밍
data: {"type": "token", "content": "메트포르민은"}

# 스트리밍 완료 (메시지 DB 저장 후)
data: {"type": "done", "message_id": 42, "created_at": "2026-06-02T10:00:00"}

# 의도 차단 - 일반 (진단요청, 처방요청 등)
data: {"type": "guardrail", "category": "PRESCRIPTION_REQUEST", "message": "약사 상담을 받으세요."}

# 의도 차단 - 응급
data: {"type": "emergency", "message": "즉시 119에 신고하거나 응급실로 가세요."}

# 의도 차단 - 자살/자해
data: {"type": "crisis", "message": "자살예방상담전화(1393)로 연락하세요."}

# LLM 응답 안전 필터 발동
data: {"type": "safety_filter", "message": "본 챗봇은 일반 정보 제공만 가능합니다."}
```

### 의도 카테고리 → 이벤트 매핑

| ChatValidationService 카테고리 | SSE 이벤트 타입 |
|-------------------------------|----------------|
| `EMERGENCY` | `emergency` |
| `SELF_HARM` | `crisis` |
| `DIAGNOSIS_REQUEST`, `PRESCRIPTION_REQUEST`, `DOSAGE_CHANGE` | `guardrail` |

---

## 5. 서비스 로직 플로우

```
ChatStreamService.stream_message(session, user, user_message)
  → AsyncGenerator[str, None]

Step 1: 사용자 메시지 ChatMessage 저장 (role=USER)

Step 2: classify_intent(user_message)
  ├── EMERGENCY → yield emergency event → 차단 메시지 저장 → return
  ├── SELF_HARM → yield crisis event   → 차단 메시지 저장 → return
  └── 기타 차단 → yield guardrail event → 차단 메시지 저장 → return

Step 3: _build_context(session, user) 호출
  - 최근 10턴 히스토리 (ChatMessage 20개, 역순 정렬)
  - 사용자 프로필 (mode + UserDisease 목록)
  - 최근 30일 가이드 (HealthGuideContent, status=COMPLETED, 최신 1건, 5000자 제한)

Step 4: OpenAI streaming 호출 (GPT-4o-mini, temp=0.7)
  └── 각 chunk → yield token event
  └── 동시에 full_response 버퍼 누적

Step 5: check_safety_expressions(full_response)
  ├── 위험 표현 발견 → yield safety_filter event
  │                    ChatMessage 저장 (blocked_by_filter=True)
  └── 정상           → ChatMessage 저장 (blocked_by_filter=False, content=full_response)

Step 6: yield done event (message_id, created_at)
```

---

## 6. 컨텍스트 빌드 상세

### 시스템 프롬프트 구조

```
당신은 의료 정보 안내 어시스턴트입니다.
- 의학적 판단(진단·처방)은 절대 하지 마세요.
- 한국어로 응답하세요.
- 일반적인 정보만 제공하고, 구체적인 의학적 결정은 의료진 상담을 권유하세요.

[사용자 정보]
모드: {mode}
등록 질환: {disease_list}  ← 없으면 섹션 생략

[최근 맞춤 안내문 - 30일 이내]
{guide_content[:5000]}  ← 없으면 섹션 전체 생략
```

### 대화 히스토리

```python
messages = await ChatMessage.filter(session=session) \
    .order_by("-created_at").limit(20)
# 역순 → 시간순 정렬 후 OpenAI messages 배열에 추가
# role: USER → "user", ASSISTANT → "assistant"
```

### 가이드 쿼리

```python
from datetime import datetime, timedelta, timezone

cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
guide = await HealthGuideContent.filter(
    user=user,
    status="COMPLETED",
    created_at__gte=cutoff,
).order_by("-created_at").first()

guide_text = guide.guide_content[:5000] if guide and guide.guide_content else None
```

---

## 7. 의존성 (import만, 수정 없음)

| 모듈 | 작성자 | 사용 방법 |
|------|-------|---------|
| `ChatValidationService` | 허승혜 | `classify_intent()`, `check_safety_expressions()` 호출 |
| `ChatMessage` | 허승혜 | `.create()`, `.filter()` |
| `ChatSession` | 허승혜 | 세션 객체 수신 (라우터에서 `ChatSessionService` 경유) |
| `ChatSessionService` | 허승혜 | `get_user_session()` 호출 |
| `UserDisease` | 허승혜 | `.filter(user=user, deleted_at=None)` |
| `HealthGuideContent` | **권순현** | `.filter(user=user, status=COMPLETED, ...)` |

---

## 8. 테스트 전략

**파일:** `app/tests/chat_stream/test_chat_stream_apis.py`

| 테스트 | 검증 내용 |
|--------|---------|
| `test_stream_normal_message` | token 이벤트 수신, done 이벤트 message_id, ChatMessage 2건 저장 |
| `test_stream_blocked_intent_guardrail` | "진단해줘" → guardrail 이벤트, blocked_by_filter=True |
| `test_stream_emergency_event` | EMERGENCY 키워드 → emergency 이벤트 |
| `test_stream_session_expired_410` | 31분 전 세션 → HTTP 410 |
| `test_stream_unauthenticated_401` | 토큰 없음 → HTTP 401 |
| `test_stream_session_not_found_404` | 없는 session_id → HTTP 404 |

**Mock 전략:**
- `openai.AsyncOpenAI` → `AsyncMock` (chunk 스트림 시뮬레이션)
- DB 모델 → 실제 SQLite (TestCase)

---

## 9. 미구현 항목 (별도 PR)

| 항목 | 이유 |
|------|------|
| Rate limiting (429) | NFR-SEC-004 별도 작업 |
| `context_summary` 필드 추가 | 마이그레이션 별도 PR, 허승혜와 협의 |
| `id` uuid vs BigInt 불일치 | ERD 작성자(허승혜)와 협의 필요 |
