"""NFR-SAFE-003 — 안전 필터 로그 응답 DTO."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.dtos.base import BaseSerializerModel


class SafetyFilterLogItem(BaseSerializerModel):
    id: uuid.UUID
    user_id: int | None
    target_type: str
    target_id: str | None
    blocked_reason: str
    message_preview: str
    filter_stage: str
    created_at: datetime

    @classmethod
    def from_orm(cls, obj: object) -> SafetyFilterLogItem:
        original_text: str = getattr(obj, "original_text", "")
        return cls(
            id=obj.id,  # type: ignore[attr-defined]
            user_id=obj.user_id,  # type: ignore[attr-defined]
            target_type=obj.target_type,  # type: ignore[attr-defined]
            target_id=obj.target_id,  # type: ignore[attr-defined]
            blocked_reason=obj.blocked_reason,  # type: ignore[attr-defined]
            message_preview=original_text[:100],
            filter_stage=obj.filter_stage,  # type: ignore[attr-defined]
            created_at=obj.created_at,  # type: ignore[attr-defined]
        )


class SafetyFilterLogListResponse(BaseSerializerModel):
    total: int
    items: list[SafetyFilterLogItem]
