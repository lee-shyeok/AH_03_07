"""REQ-AUTO-005 맞춤 안내문 생성 트리거·오케스트레이터 (Phase 3).

7단계 흐름:
  1. 데이터 수집 (DataSourceCollector)
  2. 트리거 조건 검사
  3. 고위험 게이트 평가 (highrisk_gate)
  4. HealthGuideInput 구성
  5. 안내문 생성 (guide_generator)
  6. 긴급 모달 플래그 전달
  7. 감사 로그

엔트리포인트 3개:
  - orchestrate()  — 수동 API 호출
  - on_input_changed() — 입력 변경 시 호출 (디바운스는 호출자 책임)
  - weekly_refresh() — 주간 스케줄러 (스케줄러 인프라는 Phase 4 담당)
"""

import json
from datetime import UTC, datetime

from app.auto_guide.interfaces import DataSourceCollector
from app.auto_guide.schema import (
    OrchestratorResult,
    OrchestratorStatus,
    TriggerCheckResult,
    TriggerStatus,
)
from app.auto_guide.stubs import StubDataSourceCollector
from app.core.logger import default_logger as logger
from app.guide_generator.schema import HealthGuideInput
from app.guide_generator.service import generate_guide
from app.highrisk_gate.schema import HighRiskGateInput
from app.highrisk_gate.service import evaluate_highrisk_gate

_DEFAULT_COLLECTOR: DataSourceCollector = StubDataSourceCollector()


def _check_trigger(
    autoimmune_mode: bool,
    disease_codes: list[str],
    risk_factor_summary: str | None,
    medication_list: list[str],
    risk_symptom_codes: list[str],
) -> TriggerCheckResult:
    """트리거 조건 3개 전부 충족해야 MET 반환."""
    missing: list[str] = []

    if not autoimmune_mode:
        missing.append("autoimmune_mode_not_selected")
    if not disease_codes:
        missing.append("disease_codes_not_registered")
    if not risk_factor_summary and not medication_list and not risk_symptom_codes:
        missing.append("no_input_source")

    if missing:
        return TriggerCheckResult(status=TriggerStatus.NOT_MET, missing_conditions=missing)
    return TriggerCheckResult(status=TriggerStatus.MET, missing_conditions=[])


async def orchestrate(
    user_id: int,
    collector: DataSourceCollector | None = None,
) -> OrchestratorResult:
    """맞춤 안내문 생성 오케스트레이터 (수동 트리거).

    Args:
        user_id: 대상 사용자 ID.
        collector: 데이터 소스 구현체. None이면 StubDataSourceCollector 사용.
    """
    if collector is None:
        collector = _DEFAULT_COLLECTOR

    now = datetime.now(tz=UTC)

    # Step 1: 데이터 수집
    autoimmune_mode = await collector.get_autoimmune_mode(user_id)
    disease_codes = await collector.get_disease_codes(user_id)
    risk_factor_summary = await collector.get_risk_factor_summary(user_id)
    medication_list = await collector.get_medication_list(user_id)
    activity_score_summary = await collector.get_activity_score_summary(user_id)
    risk_symptom_codes = await collector.get_risk_symptom_codes(user_id)
    upcoming_appointments = await collector.get_upcoming_appointments(user_id)
    lab_results_summary = await collector.get_lab_results_summary(user_id)
    pregnancy_lactation_codes = await collector.get_pregnancy_lactation_codes(user_id)
    vaccine_infection_prevention = await collector.get_vaccine_infection_prevention(user_id)
    checked_symptom_codes = await collector.get_checked_symptom_codes(user_id)
    self_report_codes = await collector.get_self_report_codes(user_id)
    lab_threshold_exceeded = await collector.get_lab_threshold_exceeded(user_id)

    # Step 2: 트리거 조건 검사
    trigger = _check_trigger(
        autoimmune_mode=autoimmune_mode,
        disease_codes=disease_codes,
        risk_factor_summary=risk_factor_summary,
        medication_list=medication_list,
        risk_symptom_codes=risk_symptom_codes,
    )
    if trigger.status == TriggerStatus.NOT_MET:
        logger.info(
            json.dumps(
                {
                    "event": "guide_trigger_not_met",
                    "user_id": user_id,
                    "missing_conditions": trigger.missing_conditions,
                }
            )
        )
        return OrchestratorResult(
            user_id=user_id,
            orchestrator_status=OrchestratorStatus.TRIGGER_NOT_MET,
            trigger_check=trigger,
            evaluated_at=now,
        )

    # Step 3: 고위험 게이트 평가
    gate_input = HighRiskGateInput(
        user_id=user_id,
        checked_symptom_codes=checked_symptom_codes,
        self_report_codes=self_report_codes,
        pregnancy_status_codes=pregnancy_lactation_codes,
        lab_threshold_exceeded=lab_threshold_exceeded,
    )
    gate_result = evaluate_highrisk_gate(gate_input)
    high_risk_flag = gate_result.status.value == "LOCKED"

    # Step 4: HealthGuideInput 구성
    guide_input = HealthGuideInput(
        user_id=user_id,
        disease_codes=disease_codes,
        high_risk_flag=high_risk_flag,
        high_risk_matched_items=[item.code for item in gate_result.matched_items],
        risk_factor_summary=risk_factor_summary,
        medication_list=medication_list,
        activity_score_summary=activity_score_summary,
        risk_symptom_codes=risk_symptom_codes,
        upcoming_appointments=upcoming_appointments,
        lab_results_summary=lab_results_summary,
        pregnancy_lactation_codes=pregnancy_lactation_codes,
        vaccine_infection_prevention=vaccine_infection_prevention,
    )

    # Step 5: 안내문 생성
    guide = await generate_guide(guide_input)

    # Step 6: 긴급 모달 플래그
    trigger_emergency_modal = gate_result.trigger_emergency_modal

    # Step 7: 감사 로그
    logger.info(
        json.dumps(
            {
                "event": "guide_orchestrated",
                "user_id": user_id,
                "guide_status": guide.status.value,
                "high_risk_flag": high_risk_flag,
                "trigger_emergency_modal": trigger_emergency_modal,
            }
        )
    )

    orchestrator_status = OrchestratorStatus(guide.status.value)

    return OrchestratorResult(
        user_id=user_id,
        orchestrator_status=orchestrator_status,
        trigger_emergency_modal=trigger_emergency_modal,
        guide=guide,
        trigger_check=trigger,
        evaluated_at=now,
    )


async def on_input_changed(
    user_id: int,
    collector: DataSourceCollector | None = None,
) -> OrchestratorResult:
    """입력 변경 시 안내문 재생성 트리거.

    디바운스(중복 호출 억제)는 호출자 책임.
    """
    return await orchestrate(user_id, collector=collector)


async def weekly_refresh(
    user_id: int,
    collector: DataSourceCollector | None = None,
) -> OrchestratorResult:
    """주간 정기 안내문 갱신.

    스케줄러 인프라 연동은 Phase 4 담당.
    """
    return await orchestrate(user_id, collector=collector)
