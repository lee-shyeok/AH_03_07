from enum import StrEnum

from tortoise import fields, models


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class KnowledgeDocument(models.Model):
    id = fields.BigIntField(primary_key=True)
    title = fields.CharField(max_length=200)
    filename = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    status = fields.CharEnumField(enum_type=DocumentStatus, default=DocumentStatus.PENDING)
    chunk_count = fields.IntField(null=True)
    source_organization = fields.CharField(max_length=100)
    published_year = fields.SmallIntField()
    error_message = fields.TextField(null=True)
    uploaded_by_user = fields.ForeignKeyField(
        "models.User", related_name="knowledge_documents", on_delete=fields.CASCADE
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "knowledge_base"
        unique_together = [("title", "source_organization", "published_year")]
        indexes = [("status",), ("uploaded_by_user",), ("created_at",)]
