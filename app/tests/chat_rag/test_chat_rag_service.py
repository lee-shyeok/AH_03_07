from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.chat_rag_service import RAG_SCORE_THRESHOLD, ChatRAGService


def make_chunk(
    score: float,
    text: str = "본문",
    source_title: str = "제목",
    source_organization: str = "기관",
) -> SimpleNamespace:
    return SimpleNamespace(
        score=score,
        text=text,
        source_title=source_title,
        source_organization=source_organization,
        section_title=None,
        document_id=1,
        chunk_index=0,
        page_number=1,
        published_year=2024,
    )


@pytest.fixture
def svc() -> ChatRAGService:
    return ChatRAGService()


def test_filter_by_threshold_keeps_above(svc: ChatRAGService) -> None:
    chunks = [make_chunk(0.5), make_chunk(0.47)]
    assert len(svc.filter_by_threshold(chunks)) == 2


def test_filter_by_threshold_drops_below(svc: ChatRAGService) -> None:
    chunks = [make_chunk(0.41), make_chunk(0.0)]
    assert svc.filter_by_threshold(chunks) == []


def test_filter_by_threshold_boundary(svc: ChatRAGService) -> None:
    chunk = make_chunk(RAG_SCORE_THRESHOLD)
    assert len(svc.filter_by_threshold([chunk])) == 1


def test_filter_by_threshold_empty(svc: ChatRAGService) -> None:
    assert svc.filter_by_threshold([]) == []


def test_build_context_format(svc: ChatRAGService) -> None:
    chunks = [make_chunk(0.5, text="내용A"), make_chunk(0.5, text="내용B")]
    ctx = svc.build_context(chunks)
    assert "[자료 1] 내용A" in ctx
    assert "[자료 2] 내용B" in ctx


def test_build_context_empty(svc: ChatRAGService) -> None:
    assert svc.build_context([]) == ""


def test_to_sources_field_mapping(svc: ChatRAGService) -> None:
    chunk = make_chunk(0.5, text="짧은 본문", source_title="제목", source_organization="기관")
    sources = svc.to_sources([chunk])
    # RagSource 분리 필드: "제목 — 기관" 합치기 제거, source_title/source_org 각각 매핑
    assert sources[0]["source_title"] == "제목"
    assert sources[0]["source_org"] == "기관"
    assert sources[0]["source_url"] is None
    assert sources[0]["snippet"] == "짧은 본문"


def test_to_sources_missing_optional_fields(svc: ChatRAGService) -> None:
    chunk = make_chunk(0.5, text="본문", source_title="제목", source_organization="")
    sources = svc.to_sources([chunk])
    # source_organization="" → source_org="" (빈 문자열, None 아님)
    assert sources[0]["source_title"] == "제목"
    assert sources[0]["source_org"] == ""


def test_to_sources_long_text_truncated(svc: ChatRAGService) -> None:
    long_text = "가" * 300
    chunk = make_chunk(0.5, text=long_text)
    sources = svc.to_sources([chunk])
    assert sources[0]["snippet"].endswith("...")
    assert len(sources[0]["snippet"]) == 203
