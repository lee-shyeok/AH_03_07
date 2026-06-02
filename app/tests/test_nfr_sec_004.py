"""NFR-SEC-004 — Rate Limiting 단위 테스트."""

from __future__ import annotations

from app.core.rate_limit.config import get_tier

# ── Tier 분류 ─────────────────────────────────────────────────


def test_tier_chat_sessions_is_llm() -> None:
    assert get_tier("POST", "/api/v1/chat/sessions/1/messages").name == "llm"


def test_tier_guide_generate_is_llm() -> None:
    assert get_tier("POST", "/api/v1/guide/generate").name == "llm"


def test_tier_guide_regenerate_is_llm() -> None:
    assert get_tier("POST", "/api/v1/guide/5/regenerate").name == "llm"


def test_tier_pills_recognize_is_ocr() -> None:
    assert get_tier("POST", "/api/v1/pills/recognize").name == "ocr"


def test_tier_medical_documents_ocr_is_ocr() -> None:
    assert get_tier("POST", "/api/v1/medical-documents/1/ocr-jobs").name == "ocr"


def test_tier_get_method_is_default() -> None:
    assert get_tier("GET", "/api/v1/chat/sessions/1/messages").name == "default"


def test_tier_unknown_path_is_default() -> None:
    assert get_tier("POST", "/api/v1/users/profile").name == "default"
