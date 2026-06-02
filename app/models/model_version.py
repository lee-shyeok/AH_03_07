import uuid
from enum import StrEnum

from tortoise import fields, models


class ModelVersionStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    DEPLOYED = "DEPLOYED"
    RETIRED = "RETIRED"


class ModelVersion(models.Model):
    """REQ-FEED-002 — AI 모델 버저닝 이력."""

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    model_name = fields.CharField(max_length=100)
    version = fields.CharField(max_length=20)
    description = fields.TextField(null=True)
    status = fields.CharEnumField(
        enum_type=ModelVersionStatus,
        max_length=20,
        default=ModelVersionStatus.CANDIDATE,
    )
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "model_versions"
        unique_together = (("model_name", "version"),)
