import uuid
from enum import StrEnum

from tortoise import fields, models

from app.models.prompts import PromptType


class PromptVersionStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PromptVersion(models.Model):
    """REQ-FEED-002 — 프롬프트 개선 이력.

    Prompt (현재 활성) vs PromptVersion (개선 후보 이력) 의미 분리.
    source_dataset: 어느 주간 집계에서 개선 후보로 선정됐는지 추적.
    """

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    # 기반이 된 현재 프롬프트 (null이면 신규)
    source_prompt = fields.ForeignKeyField(
        "models.Prompt",
        related_name="versions",
        on_delete=fields.SET_NULL,
        null=True,
    )
    # 어느 집계 데이터셋에서 개선 후보로 도출됐는지
    source_dataset = fields.ForeignKeyField(
        "models.ModelImprovementDataset",
        related_name="prompt_versions",
        on_delete=fields.SET_NULL,
        null=True,
    )
    prompt_type = fields.CharEnumField(enum_type=PromptType, max_length=50)
    version = fields.CharField(max_length=20)
    template_text = fields.TextField()
    improvement_reason = fields.TextField()
    status = fields.CharEnumField(
        enum_type=PromptVersionStatus,
        max_length=20,
        default=PromptVersionStatus.CANDIDATE,
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prompt_versions"
