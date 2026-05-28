"""
챗봇 라우터  REQ-CHAT-001 ~ REQ-CHAT-006

엔드포인트:
  POST   /v1/chat/sessions                     세션 시작
  GET    /v1/chat/sessions                     세션 목록 조회
  GET    /v1/chat/sessions/{id}/messages       대화 내역 조회
  POST   /v1/chat/sessions/{id}/messages       메시지 전송 (SSE 스트리밍)
  POST   /v1/chat/messages/{id}/feedback       응답 평가
"""

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from chat_engine import (
    _check_guardrail,
    build_messages,
    build_system_prompt,
    stream_chat_response,
)
from chat_models import ChatFeedback, ChatMessage, ChatSession, MessageRoleEnum
from chat_schemas import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionListItem,
    ChatSessionListResponse,
    ChatSessionResponse,
)
from database import get_db, redis_client
from guide_models import Guide, GuideStatusEnum
from medical_record_models import MedicalRecord
from models import User
from security import get_current_user_id

router = APIRouter()

SESSION_TIMEOUT_MINUTES = 30
MAX_PAGE_SIZE = 50
MAX_CONTEXT_MESSAGES = 20  # 최근 10턴

# [수정 2] 메시지 Rate Limit — 분당 30회
_MSG_RATE_KEY = "chat:msg_rate:{user_id}"
MSG_RATE_LIMIT = 30
MSG_RATE_WINDOW = 60  # 초


# ── 헬퍼 ──────────────────────────────────────────────────


def _get_session_or_404(session_id: int, user_id: int, db: Session) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return session


def _expire_if_timeout(session: ChatSession, db: Session) -> None:
    """마지막 활동 후 30분 경과 시 세션 자동 종료."""
    if not session.is_active:
        return
    now = datetime.now(UTC)
    last = session.last_activity_at
    # [수정 4] timezone naive/aware 혼용 방지
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    if now - last > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        session.is_active = False
        session.ended_at = now
        db.commit()


def _check_msg_rate_limit(user_id: int) -> None:
    """[수정 2] 메시지 Rate Limit — 분당 30회 초과 시 429."""
    key = _MSG_RATE_KEY.format(user_id=user_id)
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, MSG_RATE_WINDOW)
    results = pipe.execute()
    count = results[0]
    if count > MSG_RATE_LIMIT:
        raise HTTPException(
            status_code=429, detail=f"메시지 전송은 분당 {MSG_RATE_LIMIT}회까지 가능합니다. 잠시 후 다시 시도해주세요."
        )


def _get_recent_guides(user_id: int, db: Session) -> list:
    """최근 30일 내 active 가이드 최대 3개 조회."""
    # [수정 4] timezone-naive로 비교
    cutoff = datetime.utcnow() - timedelta(days=30)
    guides = (
        db.query(Guide, MedicalRecord.diagnosis, MedicalRecord.visit_date)
        .join(MedicalRecord, Guide.record_id == MedicalRecord.id)
        .filter(
            Guide.user_id == user_id,
            Guide.status == GuideStatusEnum.active,
            Guide.deleted_at.is_(None),
            Guide.created_at >= cutoff,
        )
        .order_by(Guide.created_at.desc())
        .limit(3)
        .all()
    )
    return [
        {
            "visit_date": str(visit_date),
            "diagnosis": diagnosis,
            "medication_guide": guide.medication_guide or "",
        }
        for guide, diagnosis, visit_date in guides
    ]


# ── 1. 세션 시작 ──────────────────────────────────────────


@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=201,
    summary="REQ-CHAT-001: 챗봇 세션 시작",
)
def create_session(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """새 챗봇 세션을 생성합니다. 기존 활성 세션은 타임아웃 체크 후 유지."""
    active_sessions = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True,
        )
        .all()
    )
    for s in active_sessions:
        _expire_if_timeout(s, db)

    session = ChatSession(user_id=user_id)
    db.add(session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="세션 생성에 실패했습니다.")
    db.refresh(session)
    return session


# ── 2. 세션 목록 조회 ─────────────────────────────────────


@router.get(
    "/chat/sessions",
    response_model=ChatSessionListResponse,
    summary="REQ-CHAT-005: 대화 세션 목록 조회",
)
def list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.created_at.desc())
    )

    total = query.count()
    sessions = query.offset((page - 1) * size).limit(size).all()

    # N+1 방지: 메시지 수 + 첫 메시지 일괄 조회
    session_ids = [s.id for s in sessions]
    msg_counts = {}
    first_msgs = {}

    if session_ids:
        counts = (
            db.query(ChatMessage.session_id, func.count(ChatMessage.id))
            .filter(ChatMessage.session_id.in_(session_ids))
            .group_by(ChatMessage.session_id)
            .all()
        )
        msg_counts = {row[0]: row[1] for row in counts}

        firsts = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id.in_(session_ids),
                ChatMessage.role == MessageRoleEnum.user,
            )
            .order_by(ChatMessage.session_id, ChatMessage.id.asc())
            .all()
        )
        seen: set = set()
        for m in firsts:
            if m.session_id not in seen:
                first_msgs[m.session_id] = m.content[:50]
                seen.add(m.session_id)

    items = [
        ChatSessionListItem(
            id=s.id,
            is_active=s.is_active,
            first_message=first_msgs.get(s.id),
            message_count=msg_counts.get(s.id, 0),
            created_at=s.created_at,
        )
        for s in sessions
    ]
    return ChatSessionListResponse(items=items, total=total, page=page, size=size)


# ── 3. 대화 내역 조회 ─────────────────────────────────────


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatHistoryResponse,
    summary="REQ-CHAT-005: 대화 내역 조회",
)
def get_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_session_or_404(session_id, user_id, db)

    query = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == user_id,
        )
        .order_by(ChatMessage.created_at.asc())
    )

    total = query.count()
    messages = query.offset((page - 1) * size).limit(size).all()

    return ChatHistoryResponse(
        session_id=session_id,
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        size=size,
    )


# ── 4. 메시지 전송 (SSE 스트리밍) ────────────────────────


@router.post(
    "/chat/sessions/{session_id}/messages",
    summary="REQ-CHAT-002: 메시지 전송 (SSE 스트리밍)",
)
async def send_message(
    session_id: int,
    body: ChatMessageRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    SSE 스트리밍으로 챗봇 응답을 실시간 전송합니다.
    Content-Type: text/event-stream
    """
    # [수정 2] Rate Limit 체크
    _check_msg_rate_limit(user_id)

    session = _get_session_or_404(session_id, user_id, db)
    _expire_if_timeout(session, db)
    if not session.is_active:
        raise HTTPException(status_code=400, detail="세션이 종료되었습니다. 새 세션을 시작해주세요.")

    user_content = body.content

    # 가드레일 체크
    guardrail_response = _check_guardrail(user_content)

    # 사용자 메시지 저장
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=MessageRoleEnum.user,
        content=user_content,
    )
    db.add(user_msg)
    session.last_activity_at = datetime.now(UTC)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="메시지 저장에 실패했습니다.")
    db.refresh(user_msg)

    # 가드레일 차단 응답
    if guardrail_response:
        assistant_msg = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=MessageRoleEnum.assistant,
            content=guardrail_response,
        )
        db.add(assistant_msg)
        db.commit()

        async def guardrail_stream():
            data = json.dumps({"content": guardrail_response, "done": True}, ensure_ascii=False)
            yield f"data: {data}\n\n"

        return StreamingResponse(guardrail_stream(), media_type="text/event-stream")

    # 컨텍스트 구성 (최근 10턴, 현재 메시지 제외)
    history_rows = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.id != user_msg.id,
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_CONTEXT_MESSAGES)
        .all()
    )
    history = [{"role": m.role.value, "content": m.content} for m in reversed(history_rows)]

    user = db.query(User).filter(User.id == user_id).first()
    recent_guides = _get_recent_guides(user_id, db)

    system_prompt = build_system_prompt(
        chronic_diseases=user.chronic_diseases if user else "",
        allergy_info=user.allergy_info if user else "",
        recent_guides=recent_guides,
    )
    messages = build_messages(system_prompt, history, user_content)

    async def event_stream():
        full_response = []
        try:
            async for chunk in stream_chat_response(messages):
                full_response.append(chunk)
                data = json.dumps({"content": chunk, "done": False}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            # 어시스턴트 응답 저장 (별도 DB 세션)
            response_text = "".join(full_response)
            if response_text.strip():
                from database import SessionLocal

                save_db = SessionLocal()
                try:
                    assistant_msg = ChatMessage(
                        session_id=session_id,
                        user_id=user_id,
                        role=MessageRoleEnum.assistant,
                        content=response_text,
                    )
                    save_db.add(assistant_msg)
                    save_db.commit()
                finally:
                    save_db.close()

        except RuntimeError:
            # [수정 3] 내부 오류 메시지 노출 방지
            error_data = json.dumps(
                {"error": "응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", "done": True},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── 5. 응답 평가 ──────────────────────────────────────────


@router.post(
    "/chat/messages/{message_id}/feedback",
    response_model=ChatFeedbackResponse,
    summary="REQ-CHAT-006: 챗봇 응답 평가",
)
def upsert_message_feedback(
    message_id: int,
    data: ChatFeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """👍/👎 평가. 이미 평가했으면 수정합니다."""
    # 메시지 소유권 + assistant 메시지만 평가 가능
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.user_id == user_id,
            ChatMessage.role == MessageRoleEnum.assistant,
        )
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    feedback = (
        db.query(ChatFeedback)
        .filter(
            ChatFeedback.message_id == message_id,
            ChatFeedback.user_id == user_id,
        )
        .first()
    )

    if feedback:
        feedback.is_positive = data.is_positive
        feedback.comment = data.comment
    else:
        feedback = ChatFeedback(
            message_id=message_id,
            user_id=user_id,
            is_positive=data.is_positive,
            comment=data.comment,
        )
        db.add(feedback)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")
    db.refresh(feedback)
    return feedback
