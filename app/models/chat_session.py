from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class ChatMode(StrEnum):
    GENERAL = "GENERAL"
    AUTOIMMUNE = "AUTOIMMUNE"


class ChatSession(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_sessions", on_delete=fields.CASCADE)
    mode = fields.CharEnumField(enum_type=ChatMode, max_length=16)
    created_at = fields.DatetimeField(auto_now_add=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "chat_sessions"
