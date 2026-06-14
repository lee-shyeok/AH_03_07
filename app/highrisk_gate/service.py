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

    # LOCKED 결정은 red_flag=True 항목만 사용.
    # non-red-flag 매칭은 안내문 컨텍스트(matched_items)로만 활용하고 차단하지 않음.
    red_flag_in_active = any(item.red_flag and item.code in active_codes for item in matched_items)
    red_flag_in_stale = any(item.red_flag and item.code in stale_codes for item in matched_items)

    if not red_flag_in_active and not red_flag_in_stale:
        # red_flag 항목 없음 → PASS (matched_items는 가이드 생성 컨텍스트용으로 유지)
        return HighRiskGateResult(
            status=GateStatus.PASS,
            matched_items=matched_items,
            trigger_emergency_modal=False,
            needs_recheck=False,
            message=_MSG_PASS,
            disclaimer=_DISCLAIMER,
            evaluated_at=datetime.now(tz=UTC),
        )

    # stale red_flag만 있고 active red_flag 없음 → 재체크 요청
    if red_flag_in_stale and not red_flag_in_active:
        return HighRiskGateResult(
            status=GateStatus.LOCKED,
            matched_items=matched_items,
            trigger_emergency_modal=False,
            needs_recheck=True,
            message=_MSG_NEEDS_RECHECK,
            disclaimer=_DISCLAIMER,
            evaluated_at=datetime.now(tz=UTC),
        )

    # active red_flag 있음 → LOCKED + 응급 모달
    return HighRiskGateResult(
        status=GateStatus.LOCKED,
        matched_items=matched_items,
        trigger_emergency_modal=True,
        needs_recheck=False,
        message=_MSG_LOCKED_EMERGENCY,
        disclaimer=_DISCLAIMER,
        evaluated_at=datetime.now(tz=UTC),
    )
