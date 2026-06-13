import json
from datetime import UTC, datetime
from pathlib import Path

from app.highrisk_gate.schema import GateStatus, HighRiskGateInput, HighRiskGateResult, MatchedItem

_RULES_PATH = Path(__file__).parent / "gate_rules.json"

# gate_rules.json 모듈 로드 시 1회 캐싱
_GATE_RULES: dict[str, dict] = {rule["code"]: rule for rule in json.loads(_RULES_PATH.read_text(encoding="utf-8"))}

_DISCLAIMER = (
    "※ 이 결과는 사용자가 직접 입력한 항목의 목록 확인이며, "
    "의료적 진단·평가·처방을 대체하지 않습니다. "
    "증상이 있으면 반드시 담당 의료진과 상담하세요."
)

_MSG_PASS = "등록된 검토 항목이 없습니다. 증상 변화가 있으면 담당 의료진과 상담하세요."
_MSG_LOCKED = (
    "담당 의료진 검토가 필요한 항목이 접수되었습니다. 자동 안내문 생성이 보류됩니다. 담당 의료진과 상담하시기 바랍니다."
)
_MSG_LOCKED_EMERGENCY = (
    "즉시 확인이 필요한 항목이 접수되었습니다. "
    "자동 안내문 생성이 보류됩니다. "
    "즉시 담당 의료진 또는 응급실에 연락하시기 바랍니다."
)
_MSG_NEEDS_RECHECK = (
    "이전 증상 체크 기록이 오래되어 재확인이 필요합니다. 자동 안내문 생성이 보류됩니다. 증상 체크를 다시 진행해 주세요."
)


def evaluate_highrisk_gate(gate_input: HighRiskGateInput) -> HighRiskGateResult:
    # stale/active 소스 분리 — stale 체크 코드는 별도 집합으로 관리
    stale_codes: set[str] = set(gate_input.checked_symptom_codes) if gate_input.checked_symptoms_is_stale else set()
    active_checked: set[str] = set() if gate_input.checked_symptoms_is_stale else set(gate_input.checked_symptom_codes)
    active_codes: set[str] = active_checked | set(gate_input.self_report_codes) | set(gate_input.pregnancy_status_codes)
    if gate_input.lab_threshold_exceeded:
        active_codes.add("LAB_THRESHOLD_EXCEEDED")

    raw_codes = active_codes | stale_codes

    # 게이트 목록 순서로 순회 — 점수·해석·추정 없음, 미등록 코드 무시, 순서 결정적
    matched_items: list[MatchedItem] = [
        MatchedItem(
            code=rule["code"],
            label=rule["label"],
            category=rule["category"],
            red_flag=rule["red_flag"],
        )
        for rule in _GATE_RULES.values()
        if rule["code"] in raw_codes
    ]

    if not matched_items:
        return HighRiskGateResult(
            status=GateStatus.PASS,
            matched_items=[],
            trigger_emergency_modal=False,
            needs_recheck=False,
            message=_MSG_PASS,
            disclaimer=_DISCLAIMER,
            evaluated_at=datetime.now(tz=UTC),
        )

    # active 소스에서 매칭된 항목이 없으면 stale-only LOCKED → 재체크 요청
    has_active_match = any(item.code in active_codes for item in matched_items)
    needs_recheck = not has_active_match

    if needs_recheck:
        return HighRiskGateResult(
            status=GateStatus.LOCKED,
            matched_items=matched_items,
            trigger_emergency_modal=False,
            needs_recheck=True,
            message=_MSG_NEEDS_RECHECK,
            disclaimer=_DISCLAIMER,
            evaluated_at=datetime.now(tz=UTC),
        )

    trigger_emergency_modal = any(item.red_flag for item in matched_items)
    message = _MSG_LOCKED_EMERGENCY if trigger_emergency_modal else _MSG_LOCKED

    return HighRiskGateResult(
        status=GateStatus.LOCKED,
        matched_items=matched_items,
        trigger_emergency_modal=trigger_emergency_modal,
        needs_recheck=False,
        message=message,
        disclaimer=_DISCLAIMER,
        evaluated_at=datetime.now(tz=UTC),
    )
