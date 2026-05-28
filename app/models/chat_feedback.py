from __future__ import annotations

from tortoise import fields, models


class ChatFeedback(models.Model):
    id = fields.BigIntField(primary_key=True)
    message = fields.ForeignKeyField("models.ChatMessage", related_name="feedbacks", on_delete=fields.CASCADE)
    score = fields.IntField()
    comment = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_feedbacks"
