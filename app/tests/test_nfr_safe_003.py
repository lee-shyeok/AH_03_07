"""NFR-SAFE-003 — 의료행위 차단 룰셋 단위 테스트."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.nfr_safe_003 import (
    SAFE_REPLACEMENT,
    apply_nfr_safe_003,
    filter_and_log,
)

# ── 패스 케이스 ────────────────────────────────────────────────


def test_clean_text_passes() -> None:
    result = apply_nfr_safe_003("루푸스 환자는 자외선 차단제를 매일 사용하는 것이 중요합니다.")
    assert result.is_blocked is False
    assert result.filtered_text == "루푸스 환자는 자외선 차단제를 매일 사용하는 것이 중요합니다."


def test_safe_consultation_phrase_passes() -> None:
    result = apply_nfr_safe_003("담당 의료진과 상담하시기 바랍니다.")
    assert result.is_blocked is False


# ── 진단명 추정 차단 ───────────────────────────────────────────


def test_diagnosis_presumption_blocked_ro_boibnida() -> None:
    result = apply_nfr_safe_003("루푸스로 보입니다.")
    assert result.is_blocked is True
    assert "diagnosis_presumption" in result.matched_categories
    assert result.filtered_text == SAFE_REPLACEMENT


def test_diagnosis_presumption_blocked_ga_uisimdbnida() -> None:
    result = apply_nfr_safe_003("류마티스관절염이 의심됩니다.")
    assert result.is_blocked is True
    assert "diagnosis_presumption" in result.matched_categories


def test_diagnosis_presumption_blocked_jindan() -> None:
    result = apply_nfr_safe_003("이 증상은 당뇨로 진단할 수 있습니다.")
    assert result.is_blocked is True
    assert "diagnosis_presumption" in result.matched_categories


# ── 약물 중단·증량·변경 차단 ──────────────────────────────────


def test_drug_stop_blocked() -> None:
    result = apply_nfr_safe_003("하이드록시클로로퀸을 중단하세요.")
    assert result.is_blocked is True
    assert "drug_modification" in result.matched_categories


def test_drug_increase_blocked() -> None:
    result = apply_nfr_safe_003("메토트렉세이트를 늘리세요.")
    assert result.is_blocked is True
    assert "drug_modification" in result.matched_categories


def test_drug_change_blocked() -> None:
    result = apply_nfr_safe_003("프레드니솔론으로 바꾸세요.")
    assert result.is_blocked is True
    assert "drug_modification" in result.matched_categories


# ── 검사 수치 판독 차단 ───────────────────────────────────────


def test_lab_dangerous_blocked() -> None:
    result = apply_nfr_safe_003("CRP 수치가 위험합니다.")
    assert result.is_blocked is True
    assert "lab_interpretation" in result.matched_categories


def test_lab_normal_blocked() -> None:
    result = apply_nfr_safe_003("혈액검사 결과가 정상입니다.")
    assert result.is_blocked is True
    assert "lab_interpretation" in result.matched_categories


# ── 치료제 선택 추천 차단 ─────────────────────────────────────


def test_treatment_recommendation_blocked() -> None:
    result = apply_nfr_safe_003("이부프로펜을 복용하세요.")
    assert result.is_blocked is True
    assert "treatment_recommendation" in result.matched_categories


def test_drug_recommendation_blocked() -> None:
    result = apply_nfr_safe_003("이 약을 추천드립니다.")
    assert result.is_blocked is True
    assert "treatment_recommendation" in result.matched_categories


# ── 질병 예후·위험도 산출 차단 ────────────────────────────────


def test_prognosis_percentage_blocked() -> None:
    result = apply_nfr_safe_003("재발할 확률이 70% 확률로 높습니다.")
    assert result.is_blocked is True
    assert "prognosis_risk" in result.matched_categories


def test_prognosis_future_risk_regex_blocked() -> None:
    result = apply_nfr_safe_003("향후 신장 합병증이 발생할 가능성이 있습니다.")
    assert result.is_blocked is True
    assert "prognosis_risk" in result.matched_categories


# ── 복수 카테고리 ─────────────────────────────────────────────


def test_multiple_categories_all_captured() -> None:
    text = "류마티스관절염으로 보입니다. 메토트렉세이트를 복용하세요."
    result = apply_nfr_safe_003(text)
    assert result.is_blocked is True
    assert "diagnosis_presumption" in result.matched_categories
    assert "treatment_recommendation" in result.matched_categories


# ── 대체 문구 검증 ────────────────────────────────────────────


def test_replacement_text_is_correct() -> None:
    result = apply_nfr_safe_003("루푸스로 보입니다.")
    assert result.filtered_text == "이 부분은 담당 의료진 또는 약사 상담이 필요합니다"


# ── filter_and_log 통합 (DB mock) ─────────────────────────────


@pytest.mark.asyncio
async def test_filter_and_log_calls_db_on_block() -> None:
    with patch("app.services.nfr_safe_003.log_safety_block", new_callable=AsyncMock) as mock_log:
        result = await filter_and_log(
            "루푸스로 보입니다.",
            user_id=1,
            target_type="CHAT",
            target_id="msg-001",
            filter_stage="post_generation",
        )
    assert result.is_blocked is True
    mock_log.assert_awaited_once()
    call_kwargs = mock_log.call_args.kwargs
    assert call_kwargs["target_type"] == "CHAT"
    assert "diagnosis_presumption" in call_kwargs["matched_categories"]


@pytest.mark.asyncio
async def test_filter_and_log_no_db_call_when_clean() -> None:
    with patch("app.services.nfr_safe_003.log_safety_block", new_callable=AsyncMock) as mock_log:
        result = await filter_and_log(
            "정기적으로 혈액검사를 받으세요.",
            user_id=1,
            target_type="GUIDE",
            filter_stage="post_generation",
        )
    assert result.is_blocked is False
    mock_log.assert_not_awaited()
