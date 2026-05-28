from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class MessageRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatMessage(models.Model):
    id = fields.BigIntField(primary_key=True)
    session = fields.ForeignKeyField("models.ChatSession", related_name="messages", on_delete=fields.CASCADE)
    role = fields.CharEnumField(enum_type=MessageRole, max_length=16)
    content = fields.TextField()
    rag_sources = fields.JSONField(default=list)
    blocked_by_filter = fields.BooleanField(default=False)
    block_reason = fields.CharField(max_length=64, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
