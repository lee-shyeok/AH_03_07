from app.highrisk_gate.schema import GateStatus, HighRiskGateInput
from app.highrisk_gate.service import evaluate_highrisk_gate

_EVAL_EXPRESSIONS = ["악화", "위험", "심각", "고위험", "자동 감지", "위험도", "심각도"]


def _make_input(**kwargs) -> HighRiskGateInput:
    defaults = dict(
        user_id=1,
        checked_symptom_codes=[],
        self_report_codes=[],
        pregnancy_status_codes=[],
        lab_threshold_exceeded=False,
    )
    defaults.update(kwargs)
    return HighRiskGateInput(**defaults)


def test_no_input_returns_pass():
    result = evaluate_highrisk_gate(_make_input())
    assert result.status == GateStatus.PASS
    assert result.matched_items == []
    assert result.trigger_emergency_modal is False


def test_non_red_flag_symptom_returns_pass_with_matched_items():
    """non-red-flag 증상은 안내문 생성을 차단하지 않음 — PASS, matched_items에는 기록."""
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["FEVER"]))
    assert result.status == GateStatus.PASS
    assert result.trigger_emergency_modal is False
    assert any(item.code == "FEVER" for item in result.matched_items)


def test_red_flag_symptom_returns_locked_with_modal():
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["DYSPNEA"]))
    assert result.status == GateStatus.LOCKED
    assert result.trigger_emergency_modal is True
    assert any(item.code == "DYSPNEA" for item in result.matched_items)


def test_mixed_red_and_non_red_flag_triggers_modal():
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["FEVER", "DYSPNEA"]))
    assert result.status == GateStatus.LOCKED
    assert result.trigger_emergency_modal is True
    codes = {item.code for item in result.matched_items}
    assert "FEVER" in codes
    assert "DYSPNEA" in codes


def test_pregnancy_status_returns_pass_with_context():
    """임신/수유는 red_flag=False → PASS, matched_items에 기록(가이드 컨텍스트용)."""
    result = evaluate_highrisk_gate(_make_input(pregnancy_status_codes=["PREGNANT"]))
    assert result.status == GateStatus.PASS
    assert result.trigger_emergency_modal is False
    assert any(item.code == "PREGNANT" for item in result.matched_items)


def test_self_report_returns_pass_with_context():
    """자가 보고 이력(결핵 등)은 red_flag=False → PASS, matched_items에 기록."""
    result = evaluate_highrisk_gate(_make_input(self_report_codes=["TB_HISTORY"]))
    assert result.status == GateStatus.PASS
    assert result.trigger_emergency_modal is False
    assert any(item.code == "TB_HISTORY" for item in result.matched_items)


def test_lab_threshold_exceeded_returns_pass():
    """검사 기준값 초과는 red_flag=False → PASS, matched_items에 기록."""
    result = evaluate_highrisk_gate(_make_input(lab_threshold_exceeded=True))
    assert result.status == GateStatus.PASS
    assert result.trigger_emergency_modal is False
    assert any(item.code == "LAB_THRESHOLD_EXCEEDED" for item in result.matched_items)


def test_unknown_code_is_ignored_returns_pass():
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["UNKNOWN_CODE_XYZ"]))
    assert result.status == GateStatus.PASS
    assert result.matched_items == []


def test_duplicate_codes_matched_once():
    """동일 코드가 여러 소스에 중복 입력돼도 matched_items에 1회만 기록."""
    result = evaluate_highrisk_gate(
        _make_input(
            checked_symptom_codes=["FEVER", "FEVER"],
            self_report_codes=["FEVER"],
        )
    )
    # FEVER는 red_flag=False → PASS
    assert result.status == GateStatus.PASS
    fever_matches = [item for item in result.matched_items if item.code == "FEVER"]
    assert len(fever_matches) == 1


def test_message_and_disclaimer_contain_no_eval_expressions():
    inputs = [
        _make_input(),
        _make_input(checked_symptom_codes=["FEVER"]),
        _make_input(checked_symptom_codes=["CHEST_PAIN"]),
    ]
    for gate_input in inputs:
        result = evaluate_highrisk_gate(gate_input)
        for expr in _EVAL_EXPRESSIONS:
            assert expr not in result.message, f"금지 표현 '{expr}' in message"
            assert expr not in result.disclaimer, f"금지 표현 '{expr}' in disclaimer"


def test_all_red_flag_codes_trigger_modal():
    red_flag_codes = ["DYSPNEA", "ALTERED_CONSCIOUSNESS", "JAUNDICE", "SEVERE_BLEEDING", "CHEST_PAIN"]
    for code in red_flag_codes:
        result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=[code]))
        assert result.trigger_emergency_modal is True, f"{code} should trigger modal"


def test_matched_item_fields_populated():
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["MOUTH_SORES"]))
    assert len(result.matched_items) == 1
    item = result.matched_items[0]
    assert item.code == "MOUTH_SORES"
    assert item.label == "입안 헐음·구내염"
    assert item.category == "SYMPTOM_CHECK"
    assert item.red_flag is False


def test_evaluated_at_is_set():
    result = evaluate_highrisk_gate(_make_input())
    assert result.evaluated_at is not None


# ── stale recheck ─────────────────────────────────────────────


def test_stale_only_match_returns_needs_recheck_no_emergency():
    """stale 체크만으로 LOCKED → needs_recheck=True, trigger_emergency_modal=False."""
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["DYSPNEA"], checked_symptoms_is_stale=True))
    assert result.status == GateStatus.LOCKED
    assert result.needs_recheck is True
    assert result.trigger_emergency_modal is False


def test_stale_non_red_flag_returns_pass():
    """stale 체크지만 red_flag=False 코드만 → PASS (차단 없음)."""
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["FEVER"], checked_symptoms_is_stale=True))
    assert result.status == GateStatus.PASS
    assert result.needs_recheck is False


def test_active_red_flag_source_overrides_stale_needs_recheck():
    """stale red_flag 체크 + active red_flag 소스 → needs_recheck=False, emergency=True."""
    result = evaluate_highrisk_gate(
        _make_input(
            checked_symptom_codes=["DYSPNEA"],
            checked_symptoms_is_stale=True,
            self_report_codes=["CHEST_PAIN"],  # red_flag=True
        )
    )
    assert result.status == GateStatus.LOCKED
    assert result.needs_recheck is False
    assert result.trigger_emergency_modal is True


def test_stale_with_no_gate_match_returns_pass():
    """stale 체크지만 게이트 미매칭 → PASS, needs_recheck=False."""
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["UNKNOWN_CODE"], checked_symptoms_is_stale=True))
    assert result.status == GateStatus.PASS
    assert result.needs_recheck is False


def test_fresh_checked_symptom_not_stale():
    """is_stale=False → 기존 동작(LOCKED, trigger_emergency_modal=True)."""
    result = evaluate_highrisk_gate(_make_input(checked_symptom_codes=["DYSPNEA"], checked_symptoms_is_stale=False))
    assert result.status == GateStatus.LOCKED
    assert result.needs_recheck is False
    assert result.trigger_emergency_modal is True
