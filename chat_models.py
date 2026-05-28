import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class ChatSession(Base):
    """챗봇 세션 — 마지막 활동 후 30분 경과 시 자동 종료"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)
    last_activity_at = Column(DateTime, server_default=func.now(), nullable=False)
    ended_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class MessageRoleEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(Base):
    """챗봇 메시지"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    role = Column(Enum(MessageRoleEnum), nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ChatFeedback(Base):
    """챗봇 응답 평가 (👍/👎)"""
    __tablename__ = "chat_feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    is_positive = Column(Boolean, nullable=False)   # True=👍, False=👎
    comment = Column(String(500), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
