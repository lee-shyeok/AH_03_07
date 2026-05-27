from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel
from app.models.user_disease import DiseaseCode
from app.models.users import UserMode


class ModeUpdateRequest(BaseModel):
    mode: UserMode


class ModeResponse(BaseSerializerModel):
    mode: UserMode


class DiseaseCreateItem(BaseModel):
    disease_code: DiseaseCode
    diagnosed_date: date | None = None
    note: str | None = Field(None, max_length=500)


class DiseaseBulkCreateRequest(BaseModel):
    diseases: list[DiseaseCreateItem] = Field(..., min_length=1)


class DiseaseUpdateRequest(BaseModel):
    diagnosed_date: date | None = None
    note: str | None = Field(None, max_length=500)


class DiseaseResponse(BaseSerializerModel):
    id: int
    disease_code: DiseaseCode
    diagnosed_date: date | None
    note: str | None
    created_at: datetime
