from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PillCandidate(BaseModel):
    drug_name: str
    confidence: float


class PillRecognizeResponse(BaseModel):
    recognition_id: int
    candidates: list[PillCandidate]
    user_confirm_required: bool = True


class PillConfirmRequest(BaseModel):
    selected_drug_name: str


class PillRecognitionHistoryItem(BaseModel):
    id: int
    image_url: str
    candidates: list[PillCandidate] | None
    selected_drug_name: str | None
    user_confirmed: bool
    created_at: datetime