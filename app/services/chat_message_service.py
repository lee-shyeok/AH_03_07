from __future__ import annotations

from datetime import datetime, timedelta

from app.models.chat_message import ChatMessage, MessageRole
from app.models.chat_session import ChatMode, ChatSession
from app.services.chat_rag_service import ChatRAGService
from app.services.chat_validation_service import BlockReason, ChatValidationService


class ChatMessageService:
    def __init__(
        self,
        validation: ChatValidationService | None = None,
        rag: ChatRAGService | None = None,
    ) -> None:
        self._validation = validation or ChatValidationService()
        self._rag = rag or ChatRAGService()

    async def _build_user_profile(self, session: ChatSession) -> dict | None:
        """REQ-CHAT-007: 사용자 프로필·약물 수집 (일반·자가면역 모드 공통 + 모드별 추가)"""
        try:
            user = await session.user
            profile: dict = {}
            is_autoimmune = session.mode == ChatMode.AUTOIMMUNE

            # 공통: 복용 약물 (최대 5개)
            meds = await user.medications.all().limit(5)  # type: ignore
            if meds:
                profile["medications"] = [
                    getattr(m, "drug_name_user_input", None) or getattr(m, "drug_name", None) or "" for m in meds
                ]

            # 공통: 최근 가이드 주제
            cutoff = datetime.utcnow() - timedelta(days=30)
            guides = await user.auto_guides.filter(created_at__gte=cutoff).order_by("-created_at").limit(3)  # type: ignore
            if guides:
                profile["recent_guide_topics"] = [
                    getattr(g, "symptom_summary", None) or getattr(g, "medication_general", None) or "" for g in guides
                ]

            if is_autoimmune:
                # 자가면역 전용: 질환·활성도
                disease = await user.diseases.filter(is_primary=True).first()  # type: ignore
                if disease:
                    profile["disease"] = getattr(disease, "disease_name", None) or getattr(disease, "name", None)
                activity = await user.activity_logs.order_by("-log_date").first()  # type: ignore
                if activity:
                    profile["recent_activity"] = {
                        "pain": getattr(activity, "pain_vas", "-"),
                        "fatigue": getattr(activity, "fatigue", "-"),
                        "difficulty": getattr(activity, "daily_difficulty", "-"),
                    }
            else:
                # 일반 모드 전용: 최근 진료기록·건강수치
                records = await user.medical_records.order_by("-visit_date").limit(3)  # type: ignore
                if records:
                    profile["recent_records"] = [
                        {
                            "hospital": getattr(r, "hospital_name", ""),
                            "diagnosis": getattr(r, "diagnosis", ""),
                        }
                        for r in records
                    ]
                metrics = await user.health_metrics.order_by("-measured_at").limit(3)  # type: ignore
                if metrics:
                    profile["recent_health_metrics"] = [
                        {
                            "type": getattr(m, "metric_type", ""),
                            "value": str(getattr(m, "user_recorded_value", "")),
                        }
                        for m in metrics
                    ]

            return profile if profile else None
        except Exception:
            return None

    async def _get_conversation_history(self, session: ChatSession) -> list[dict]:
        """최근 10턴(사용자 5 + 어시스턴트 5) 대화 이력"""
        try:
            messages = await ChatMessage.filter(session=session).order_by("-created_at").limit(10)
            history = []
            for m in reversed(messages):
                history.append(
                    {
                        "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                        "content": m.content,
                    }
                )
            return history
        except Exception:
            return []

    async def handle_message(self, session: ChatSession, user_message: str) -> ChatMessage:
        # 1. 사용자 메시지 저장
        await ChatMessage.create(
            session=session,
            role=MessageRole.USER,
            content=user_message,
            rag_sources=[],
            blocked_by_filter=False,
        )

        # 2. 의도 분류 → 차단 시 즉시 반환
        intent = self._validation.classify_intent(user_message)
        if intent is not None:
            return await self._save_blocked(session, BlockReason.INTENT_BLOCKED)

        # 3. 사용자 프로필 + 대화 이력 수집 (REQ-CHAT-007)
        user_profile = await self._build_user_profile(session)
        conversation_history = await self._get_conversation_history(session)

        # 4. RAG 생성 (개인화 컨텍스트 포함)
        result = await self._rag.generate_response(
            user_message,
            user_profile=user_profile,
            conversation_history=conversation_history,
        )
        answer: str = result["answer"]
        is_general_info: bool = result["is_general_info"]
        sources: list[dict] = result["sources"]

        # 5. 응답 안전 표현 검사
        if self._validation.check_safety_expressions(answer) is not None:
            return await self._save_blocked(session, BlockReason.SAFETY_FILTER)

        # 6. AUTOIMMUNE 모드 + 출처 없음 → "[일반 정보]" 라벨
        if session.mode == ChatMode.AUTOIMMUNE and is_general_info:
            answer = f"[일반 정보] {answer}"

        # 7. 어시스턴트 메시지 저장
        return await ChatMessage.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=answer,
            rag_sources=sources,
            blocked_by_filter=False,
        )

    async def _save_blocked(self, session: ChatSession, reason: BlockReason) -> ChatMessage:
        refusal = self._validation.get_refusal_message(reason)
        return await ChatMessage.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=refusal,
            rag_sources=[],
            blocked_by_filter=True,
            block_reason=reason,
        )

    async def get_messages(self, session: ChatSession, page: int, size: int) -> tuple[list[ChatMessage], int]:
        query = ChatMessage.filter(session=session).order_by("created_at")
        total = await query.count()
        messages = await query.offset((page - 1) * size).limit(size)
        return messages, total


def get_chat_message_service() -> ChatMessageService:
    return ChatMessageService()
