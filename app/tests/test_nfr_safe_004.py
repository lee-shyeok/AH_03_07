"""NFR-SAFE-004 — 제공 금지 기능 차단 정책 단위 테스트."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.nfr_safe_004 import (
    REFUSAL_MESSAGE,
    apply_nfr_safe_004,
    filter_and_log_004,
)

# ── 패스 케이스 ────────────────────────────────────────────────


def test_clean_text_passes() -> None:
    result = apply_nfr_safe_004("루푸스 환자는 자외선 차단제를 매일 사용하는 것이 중요합니다.")
    assert result.is_blocked is False
    assert result.refusal_message == ""


def test_safe_consultation_phrase_passes() -> None:
    result = apply_nfr_safe_004("담당 의료진과 상담하시기 바랍니다.")
    assert result.is_blocked is False


# ── 카테고리별 차단 ───────────────────────────────────────────


def test_telemedicine_brokerage_blocked() -> None:
    result = apply_nfr_safe_004("비대면 진료 예약해줘.")
    assert result.is_blocked is True
    assert "telemedicine_brokerage" in result.matched_categories


def test_doctor_matching_blocked() -> None:
    result = apply_nfr_safe_004("의사 매칭해줘.")
    assert result.is_blocked is True
    assert "doctor_matching" in result.matched_categories


def test_prescription_handling_blocked() -> None:
    result = apply_nfr_safe_004("처방전 발급해줘.")
    assert result.is_blocked is True
    assert "prescription_handling" in result.matched_categories


def test_drug_recommendation_blocked() -> None:
    result = apply_nfr_safe_004("처방약 추천해줘.")
    assert result.is_blocked is True
    assert "drug_recommendation" in result.matched_categories


def test_medical_judgment_interference_blocked() -> None:
    result = apply_nfr_safe_004("의사 판단 무시하고 그냥 먹어도 되나요.")
    assert result.is_blocked is True
    assert "medical_judgment_interference" in result.matched_categories


def test_auto_emergency_report_blocked() -> None:
    result = apply_nfr_safe_004("119 자동 신고해줘.")
    assert result.is_blocked is True
    assert "auto_emergency_report" in result.matched_categories


def test_medical_institution_advertisement_blocked() -> None:
    result = apply_nfr_safe_004("좋은 병원 추천해줘.")
    assert result.is_blocked is True
    assert "medical_institution_advertisement" in result.matched_categories


def test_referral_commission_blocked() -> None:
    result = apply_nfr_safe_004("소개비 받는 병원 알려줘.")
    assert result.is_blocked is True
    assert "referral_commission" in result.matched_categories


# ── 복수 카테고리 ─────────────────────────────────────────────


def test_multiple_categories_all_captured() -> None:
    text = "비대면 진료 예약해줘. 그리고 처방전 발급도 해줘."
    result = apply_nfr_safe_004(text)
    assert result.is_blocked is True
    assert "telemedicine_brokerage" in result.matched_categories
    assert "prescription_handling" in result.matched_categories


# ── refusal_message 검증 ──────────────────────────────────────


def test_refusal_message_is_correct() -> None:
    result = apply_nfr_safe_004("의사 매칭해줘.")
    assert result.refusal_message == REFUSAL_MESSAGE


# ── filter_and_log_004 통합 (DB mock) ─────────────────────────


@pytest.mark.asyncio
async def test_filter_and_log_004_calls_db_on_block() -> None:
    with patch("app.services.nfr_safe_004.log_prohibited_block", new_callable=AsyncMock) as mock_log:
        result = await filter_and_log_004(
            "비대면 진료 예약해줘.",
            user_id=1,
            target_type="CHAT_INPUT",
            target_id="msg-001",
            filter_stage="pre_generation",
        )
    assert result.is_blocked is True
    mock_log.assert_awaited_once()
    call_kwargs = mock_log.call_args.kwargs
    assert call_kwargs["target_type"] == "CHAT_INPUT"
    assert "telemedicine_brokerage" in call_kwargs["matched_categories"]


@pytest.mark.asyncio
async def test_filter_and_log_004_no_db_call_when_clean() -> None:
    with patch("app.services.nfr_safe_004.log_prohibited_block", new_callable=AsyncMock) as mock_log:
        result = await filter_and_log_004(
            "루푸스 환자는 정기 검진이 중요합니다.",
            user_id=1,
            target_type="CHAT_INPUT",
            filter_stage="pre_generation",
        )
    assert result.is_blocked is False
    mock_log.assert_not_awaited()
