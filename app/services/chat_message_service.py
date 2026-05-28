from __future__ import annotations

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

    async def handle_message(self, session: ChatSession, user_message: str) -> ChatMessage:
        # 1. 사용자 메시지 저장
        await ChatMessage.create(
            session=session,
            role=MessageRole.USER,
            content=user_message,
            rag_sources=[],
            blocked_by_filter=False,
        )

        # 2. 의도 분류 → 차단 시 즉시 반환 (RAG 호출 안 함)
        intent = self._validation.classify_intent(user_message)
        if intent is not None:
            return await self._save_blocked(session, BlockReason.INTENT_BLOCKED)

        # 3. RAG 생성
        result = await self._rag.generate_response(user_message)
        answer: str = result["answer"]
        is_general_info: bool = result["is_general_info"]
        sources: list[dict] = result["sources"]

        # 4. 응답 안전 표현 검사
        if self._validation.check_safety_expressions(answer) is not None:
            return await self._save_blocked(session, BlockReason.SAFETY_FILTER)

        # 5. KB-003: AUTOIMMUNE 모드 + 출처 없음 → "[일반 정보]" 라벨
        if session.mode == ChatMode.AUTOIMMUNE and is_general_info:
            answer = f"[일반 정보] {answer}"

        # 6. 어시스턴트 메시지 저장
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


def get_chat_message_service() -> ChatMessageService:
    return ChatMessageService()
