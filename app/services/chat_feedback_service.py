from __future__ import annotations

from app.models.chat_feedback import ChatFeedback
from app.models.chat_message import ChatMessage
from app.models.users import User


class ChatFeedbackService:
    async def record_feedback(
        self,
        user: User,
        message_id: int,
        score: int,
        comment: str | None = None,
    ) -> ChatFeedback | None:
        message = await ChatMessage.get_or_none(
            id=message_id,
            session__user=user,
            session__deleted_at=None,
        )
        if message is None:
            return None
        feedback, _ = await ChatFeedback.update_or_create(
            message=message,
            defaults={"score": score, "comment": comment},
        )
        return feedback
