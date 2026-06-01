from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from app.models.chat_message import ChatMessage, MessageRole
from app.models.chat_session import ChatSession
from app.models.health_guides import GuideStatus, HealthGuideContent
from app.models.user_disease import UserDisease
from app.models.users import User
from app.services.chat_validation_service import ChatValidationService

SESSION_EXPIRE_MINUTES = 30
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
GUIDE_MAX_CHARS = 5000
HISTORY_LIMIT = 20  # 10턴 × 2 (USER + ASSISTANT)

_EMERGENCY_CATEGORIES = frozenset({"EMERGENCY"})
_CRISIS_CATEGORIES = frozenset({"SELF_HARM"})
_GUARDRAIL_MESSAGES: dict[str, str] = {
    "PRESCRIPTION_REQUEST": "이 질문은 약사 상담이 필요합니다.",
    "DIAGNOSIS_REQUEST": "이 질문은 의사 진료가 필요합니다.",
    "DOSAGE_CHANGE": "약 복용량 변경은 반드시 의료진과 상담하세요.",
}
_DEFAULT_GUARDRAIL = "이 질문은 의료진의 직접 상담이 필요합니다."
_EMERGENCY_MSG = "즉시 119에 신고하거나 응급실로 가세요."
_CRISIS_MSG = "자살예방상담전화(1393)로 연락하세요."
_SYSTEM_BASE = """당신은 의료 정보 안내 어시스턴트입니다.
- 의학적 판단(진단·처방)은 절대 하지 마세요.
- 한국어로 응답하세요.
- 일반적인 정보만 제공하고, 구체적인 의학적 결정은 의료진 상담을 권유하세요."""


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class ChatStreamService:
    def __init__(self) -> None:
        self._validation = ChatValidationService()

    def is_session_expired(self, session: ChatSession) -> bool:
        created = session.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        return datetime.now(tz=UTC) > created + timedelta(minutes=SESSION_EXPIRE_MINUTES)

    async def stream_message(
        self, session: ChatSession, user: User, user_message: str
    ) -> AsyncIterator[str]:
        # Task 3~5에서 순차 구현 — 임시 placeholder
        yield _sse({"type": "done", "message_id": 0, "created_at": ""})

    def _make_block_event(self, category: str) -> tuple[dict, str]:
        if category in _EMERGENCY_CATEGORIES:
            return {"type": "emergency", "message": _EMERGENCY_MSG}, _EMERGENCY_MSG
        if category in _CRISIS_CATEGORIES:
            return {"type": "crisis", "message": _CRISIS_MSG}, _CRISIS_MSG
        msg = _GUARDRAIL_MESSAGES.get(category, _DEFAULT_GUARDRAIL)
        return {"type": "guardrail", "category": category, "message": msg}, msg

    async def _build_context(
        self, session: ChatSession, user: User
    ) -> tuple[str, list[dict]]:
        recent = await ChatMessage.filter(session=session).order_by("-created_at").limit(HISTORY_LIMIT)
        history = [
            {
                "role": "user" if m.role == MessageRole.USER else "assistant",
                "content": m.content,
            }
            for m in reversed(recent)
        ]
        diseases = await UserDisease.filter(user=user, deleted_at=None)
        disease_part = ""
        if diseases:
            names = ", ".join(d.disease_code for d in diseases)
            disease_part = f"\n등록 질환: {names}"
        cutoff = datetime.now(tz=UTC) - timedelta(days=30)
        guide = await HealthGuideContent.filter(
            user=user,
            status=GuideStatus.COMPLETED,
            created_at__gte=cutoff,
        ).order_by("-created_at").first()
        guide_part = ""
        if guide and guide.guide_content:
            guide_part = f"\n\n[최근 맞춤 안내문 - 30일 이내]\n{guide.guide_content[:GUIDE_MAX_CHARS]}"
        system_prompt = (
            f"{_SYSTEM_BASE}\n\n"
            f"[사용자 정보]\n모드: {session.mode}{disease_part}"
            f"{guide_part}"
        )
        return system_prompt, history
