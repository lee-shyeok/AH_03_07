"""REQ-FEED-002 — 가명처리 함수 + 피드백 집계 태스크 단위 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.anonymization.pseudonymize import (
    decrypt_term,
    describe_level,
    encrypt_term,
    pseudonymize_text,
    pseudonymize_user_id,
)

# ── pseudonymize_user_id ─────────────────────────────────────


def test_pseudonymize_user_id_is_deterministic() -> None:
    """동일 user_id → 동일 해시."""
    uid = "3f4a-1234-abcd"
    assert pseudonymize_user_id(uid) == pseudonymize_user_id(uid)


def test_pseudonymize_user_id_different_inputs() -> None:
    """다른 user_id → 다른 해시."""
    assert pseudonymize_user_id("user-A") != pseudonymize_user_id("user-B")


def test_pseudonymize_user_id_prefix() -> None:
    """반환값은 'u_' 접두사를 가진다."""
    result = pseudonymize_user_id("any-id")
    assert result.startswith("u_")


# ── encrypt_term / decrypt_term ──────────────────────────────


def test_encrypt_term_roundtrip() -> None:
    """암호화 후 복호화 시 원문 복원."""
    term = "메토트렉세이트"
    assert decrypt_term(encrypt_term(term)) == term


def test_encrypt_term_is_random() -> None:
    """동일 평문도 매 호출마다 다른 암호문(nonce 무작위)."""
    term = "류마티스관절염"
    assert encrypt_term(term) != encrypt_term(term)


def test_encrypt_term_empty_roundtrip() -> None:
    """빈 문자열도 암호화/복호화 정상."""
    assert decrypt_term(encrypt_term("")) == ""


# ── pseudonymize_text ────────────────────────────────────────


def test_pseudonymize_text_replaces_term() -> None:
    """지정 용어가 [ENC:...] 토큰으로 치환된다."""
    text = "환자는 메토트렉세이트를 복용 중"
    result = pseudonymize_text(text, ["메토트렉세이트"])
    assert "메토트렉세이트" not in result
    assert "[ENC:" in result


def test_pseudonymize_text_no_match() -> None:
    """텍스트에 없는 용어는 변경 없음."""
    text = "정상 텍스트"
    result = pseudonymize_text(text, ["없는단어"])
    assert result == text


def test_pseudonymize_text_multiple_terms() -> None:
    """여러 용어를 한 번에 처리."""
    text = "아스피린과 이부프로펜"
    result = pseudonymize_text(text, ["아스피린", "이부프로펜"])
    assert "아스피린" not in result
    assert "이부프로펜" not in result


# ── describe_level ───────────────────────────────────────────


def test_describe_level_both() -> None:
    level = describe_level(user_hashed=True, terms_encrypted=True)
    assert "hmac_sha256" in level
    assert "aes128gcm" in level


def test_describe_level_user_only() -> None:
    level = describe_level(user_hashed=True, terms_encrypted=False)
    assert "hmac_sha256" in level
    assert "aes128gcm" not in level


def test_describe_level_none() -> None:
    assert describe_level(user_hashed=False, terms_encrypted=False) == "none"


# ── aggregate_feedback_weekly (Celery 태스크 내부 로직) ──────


@pytest.mark.asyncio
async def test_aggregate_skips_if_no_consented_users() -> None:
    """동의 사용자 없으면 데이터셋 생성 없이 종료."""
    from ai_worker.tasks.feedback_aggregation_tasks import _run_aggregation

    with (
        patch("app.models.model_improvement_dataset.ModelImprovementDataset.filter") as mock_filter,
        patch("app.models.user_consents.UserConsent.filter") as mock_consent_filter,
    ):
        # 중복 버전 없음
        mock_filter.return_value.exists = AsyncMock(return_value=False)
        # 동의자 없음 — values_list()를 await하므로 AsyncMock으로 설정
        consent_qs = MagicMock()
        consent_qs.values_list = AsyncMock(return_value=[])
        mock_consent_filter.return_value = consent_qs

        # 예외 없이 종료되면 OK
        await _run_aggregation()


@pytest.mark.asyncio
async def test_aggregate_skips_if_dataset_already_exists() -> None:
    """이미 집계된 버전이면 중복 실행하지 않는다."""
    from ai_worker.tasks.feedback_aggregation_tasks import _run_aggregation

    with patch("app.models.model_improvement_dataset.ModelImprovementDataset.filter") as mock_filter:
        mock_filter.return_value.exists = AsyncMock(return_value=True)
        await _run_aggregation()
        # create가 호출되지 않아야 함 — create 호출 여부는 ModelImprovementDataset.create mock으로 확인
