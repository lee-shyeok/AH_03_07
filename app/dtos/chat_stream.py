from __future__ import annotations

from pydantic import BaseModel, field_validator


class StreamMessageRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if len(v) < 1:
            raise ValueError("message must be at least 1 character")
        if len(v) > 4000:
            raise ValueError("message must be at most 4000 characters")
        return v
