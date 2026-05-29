from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.prompts import PromptType


class PromptCreateRequest(BaseModel):
    prompt_type: PromptType
    name: str
    version: str = "v1.0"
    template_text: str
    variables: dict | None = None
    is_active: bool = True


class PromptUpdateRequest(BaseModel):
    name: str | None = None
    template_text: str | None = None
    variables: dict | None = None
    is_active: bool | None = None


class PromptResponse(BaseModel):
    id: UUID
    prompt_type: PromptType
    name: str
    version: str
    template_text: str
    variables: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptListResponse(BaseModel):
    prompts: list[PromptResponse]
    total: int
