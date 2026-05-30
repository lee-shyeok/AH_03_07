from __future__ import annotations

from app.models.chat_session import ChatMode, ChatSession
from app.models.users import User, UserMode

_USER_MODE_TO_CHAT_MODE: dict[UserMode, ChatMode] = {
    UserMode.GENERAL: ChatMode.GENERAL,
    UserMode.AUTOIMMUNE: ChatMode.AUTOIMMUNE,
}


class ChatSessionService:
    async def create_session(self, user: User) -> ChatSession:
        chat_mode = _USER_MODE_TO_CHAT_MODE.get(user.mode, ChatMode.GENERAL)
        return await ChatSession.create(user=user, mode=chat_mode)

    async def get_user_session(self, user: User, session_id: int) -> ChatSession | None:
        return await ChatSession.get_or_none(
            id=session_id,
            user=user,
            deleted_at=None,
        )
