"""REQ-AUTO-005 오케스트레이터 단위 테스트.

모든 외부 서비스(guide_generator, highrisk_gate, DataSourceCollector)는 AsyncMock/MagicMock으로 대체.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auto_guide.schema import OrchestratorStatus, TriggerStatus
from app.auto_guide.service import _check_trigger, on_input_changed, orchestrate, weekly_refresh
from app.guide_generator.schema import GuideStatus, HealthGuideInput, HealthGuideOutput

# ── 공통 픽스처 ──────────────────────────────────────────────────

_FAKE_CREATED_AT = datetime(2026, 5, 27, 0, 0, 0, tzinfo=UTC)


def _make_guide(status: GuideStatus) -> HealthGuideOutput:
    return HealthGuideOutput(
        user_id=1,
        status=status,
        medication_general="약물 복용 시 의료진 지시를 따르세요.",
        side_effect_monitoring=["두통이 생기면 의료진에게 알려주세요."],
        lifestyle_info="규칙적인 생활을 유지하세요.",
        symptom_summary="증상 변화를 다음 진료 시 공유하세요.",
        sources=[],
        disclaimer="※ 이 안내문은 의료 진단·처방·치료를 대체하지 않습니다.",
        created_at=_FAKE_CREATED_AT,
    )


def _make_gate_result(locked: bool = False, emergency: bool = False, needs_recheck: bool = False) -> MagicMock:
    gate_result = MagicMock()
    gate_result.status.value = "LOCKED" if locked else "PASS"
    gate_result.matched_items = []
    gate_result.trigger_emergency_modal = emergency
    gate_result.needs_recheck = needs_recheck
    return gate_result


def _make_collector(
    autoimmune_mode: bool = True,
    disease_codes: list[str] | None = None,
    risk_factor_summary: str | None = "위험 요인 없음",
    medication_list: list[str] | None = None,
    risk_symptom_codes: list[str] | None = None,
    pregnancy_lactation_codes: list[str] | None = None,
    checked_symptom_codes: list[str] | None = None,
    self_report_codes: list[str] | None = None,
    lab_threshold_exceeded: bool = False,
) -> MagicMock:
    collector = MagicMock()
    collector.get_autoimmune_mode = AsyncMock(return_value=autoimmune_mode)
    collector.get_disease_codes = AsyncMock(return_value=disease_codes or ["RA"])
    collector.get_risk_factor_summary = AsyncMock(return_value=risk_factor_summary)
    collector.get_medication_list = AsyncMock(return_value=medication_list or [])
    collector.get_activity_score_summary = AsyncMock(return_value=None)
    collector.get_risk_symptom_codes = AsyncMock(return_value=risk_symptom_codes or [])
    collector.get_upcoming_appointments = AsyncMock(return_value=[])
    collector.get_lab_results_summary = AsyncMock(return_value=None)
    collector.get_pregnancy_lactation_codes = AsyncMock(return_value=pregnancy_lactation_codes or [])
    collector.get_vaccine_infection_prevention = AsyncMock(return_value=None)
    collector.get_checked_symptom_codes = AsyncMock(return_value=(checked_symptom_codes or [], False))
    collector.get_self_report_codes = AsyncMock(return_value=self_report_codes or [])
    collector.get_lab_threshold_exceeded = AsyncMock(return_value=lab_threshold_exceeded)
    return collector


# ── 트리거 조건 검사 ─────────────────────────────────────────────


def test_trigger_met_when_all_conditions_satisfied():
    """모드·질환·입력 소스 3개 모두 충족 → MET."""
    result = _check_trigger(
        autoimmune_mode=True,
        disease_codes=["RA"],
        risk_factor_summary="위험 없음",
        medication_list=[],
        risk_symptom_codes=[],
    )
    assert result.status == TriggerStatus.MET
    assert result.missing_conditions == []


def test_trigger_not_met_when_mode_off():
    """자가면역 모드 미선택 → NOT_MET."""
    result = _check_trigger(
        autoimmune_mode=False,
        disease_codes=["RA"],
        risk_factor_summary="위험 없음",
        medication_list=[],
        risk_symptom_codes=[],
    )
    assert result.status == TriggerStatus.NOT_MET
    assert "autoimmune_mode_not_selected" in result.missing_conditions


def test_trigger_not_met_when_no_disease_codes():
    """질환 코드 미등록 → NOT_MET."""
    result = _check_trigger(
        autoimmune_mode=True,
        disease_codes=[],
        risk_factor_summary="위험 없음",
        medication_list=[],
        risk_symptom_codes=[],
    )
    assert result.status == TriggerStatus.NOT_MET
    assert "disease_codes_not_registered" in result.missing_conditions


def test_trigger_not_met_when_no_input_source():
    """입력 소스(위험요인·약물·증상) 3개 모두 없음 → NOT_MET."""
    result = _check_trigger(
        autoimmune_mode=True,
        disease_codes=["RA"],
        risk_factor_summary=None,
        medication_list=[],
        risk_symptom_codes=[],
    )
    assert result.status == TriggerStatus.NOT_MET
    assert "no_input_source" in result.missing_conditions


# ── orchestrate() ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orchestrate_trigger_not_met_returns_early():
    """트리거 조건 미충족 → TRIGGER_NOT_MET, generate_guide 미호출."""
    collector = _make_collector(autoimmune_mode=False)

    with patch("app.auto_guide.service.generate_guide") as mock_gen:
        result = await orchestrate(user_id=1, collector=collector)

    mock_gen.assert_not_called()
    assert result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET
    assert result.guide is None
    assert result.trigger_check is not None
    assert result.trigger_check.status == TriggerStatus.NOT_MET


@pytest.mark.asyncio
async def test_orchestrate_generated_guide():
    """트리거 충족 + 게이트 PASS + LLM 성공 → GENERATED, generate_guide에 high_risk_flag=False 전달."""
    collector = _make_collector()
    mock_gen = AsyncMock(return_value=_make_guide(GuideStatus.GENERATED))

    with (
        patch("app.auto_guide.service.evaluate_highrisk_gate", return_value=_make_gate_result()),
        patch("app.auto_guide.service.generate_guide", mock_gen),
    ):
        result = await orchestrate(user_id=1, collector=collector)

    assert result.orchestrator_status == OrchestratorStatus.GENERATED
    assert result.guide is not None
    assert result.trigger_emergency_modal is False

    called_input: HealthGuideInput = mock_gen.call_args.args[0]
    assert called_input.high_risk_flag is False


@pytest.mark.asyncio
async def test_orchestrate_high_risk_sets_flag():
    """게이트 LOCKED → generate_guide에 high_risk_flag=True 전달, BLOCKED_HIGH_RISK 반환."""
    collector = _make_collector()
    mock_gen = AsyncMock(return_value=_make_guide(GuideStatus.BLOCKED_HIGH_RISK))

    locked_gate = _make_gate_result(locked=True, emergency=True)
    matched = MagicMock()
    matched.code = "DYSPNEA"
    locked_gate.matched_items = [matched]

    with (
        patch("app.auto_guide.service.evaluate_highrisk_gate", return_value=locked_gate),
        patch("app.auto_guide.service.generate_guide", mock_gen),
    ):
        result = await orchestrate(user_id=1, collector=collector)

    assert result.orchestrator_status == OrchestratorStatus.BLOCKED_HIGH_RISK
    assert result.trigger_emergency_modal is True

    called_input: HealthGuideInput = mock_gen.call_args.args[0]
    assert called_input.high_risk_flag is True


@pytest.mark.asyncio
async def test_orchestrate_generation_failed():
    """게이트 PASS + generate_guide가 GENERATION_FAILED 반환 → 크래시 없이 GENERATION_FAILED."""
    collector = _make_collector()
    mock_gen = AsyncMock(return_value=_make_guide(GuideStatus.GENERATION_FAILED))

    with (
        patch("app.auto_guide.service.evaluate_highrisk_gate", return_value=_make_gate_result()),
        patch("app.auto_guide.service.generate_guide", mock_gen),
    ):
        result = await orchestrate(user_id=1, collector=collector)

    assert result.orchestrator_status == OrchestratorStatus.GENERATION_FAILED
    assert result.guide is not None
    assert result.guide.status == GuideStatus.GENERATION_FAILED


@pytest.mark.asyncio
async def test_orchestrate_self_report_and_lab_forwarded_to_gate():
    """get_self_report_codes / get_lab_threshold_exceeded → HighRiskGateInput에 정확히 전달."""
    collector = _make_collector(
        self_report_codes=["TB_HISTORY", "HEPATITIS_HISTORY"],
        lab_threshold_exceeded=True,
    )
    mock_gen = AsyncMock(return_value=_make_guide(GuideStatus.GENERATED))

    with (
        patch("app.auto_guide.service.evaluate_highrisk_gate") as mock_gate,
        patch("app.auto_guide.service.generate_guide", mock_gen),
    ):
        mock_gate.return_value = _make_gate_result()
        await orchestrate(user_id=1, collector=collector)

    gate_call_input = mock_gate.call_args.args[0]
    assert gate_call_input.self_report_codes == ["TB_HISTORY", "HEPATITIS_HISTORY"]
    assert gate_call_input.lab_threshold_exceeded is True


@pytest.mark.asyncio
async def test_on_input_changed_delegates_to_orchestrate():
    """on_input_changed → orchestrate 위임."""
    collector = _make_collector(autoimmune_mode=False)

    with patch("app.auto_guide.service.generate_guide") as mock_gen:
        result = await on_input_changed(user_id=1, collector=collector)

    mock_gen.assert_not_called()
    assert result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET


@pytest.mark.asyncio
async def test_weekly_refresh_delegates_to_orchestrate():
    """weekly_refresh → orchestrate 위임."""
    collector = _make_collector(autoimmune_mode=False)

    with patch("app.auto_guide.service.generate_guide") as mock_gen:
        result = await weekly_refresh(user_id=1, collector=collector)

    mock_gen.assert_not_called()
    assert result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET
