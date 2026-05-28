from dataclasses import asdict, dataclass
from datetime import datetime

from app.dtos.base import BaseSerializerModel
from app.models.knowledge import DocumentStatus


@dataclass
class KnowledgeChunk:
    document_id: int
    chunk_index: int
    text: str
    score: float
    page_number: int
    section_title: str | None
    source_title: str
    source_organization: str
    published_year: int

    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeDocumentResponse(BaseSerializerModel):
    id: int
    title: str
    filename: str
    status: DocumentStatus
    chunk_count: int | None
    source_organization: str
    published_year: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentUploadResponse(BaseSerializerModel):
    document_id: int
    title: str
    status: DocumentStatus
