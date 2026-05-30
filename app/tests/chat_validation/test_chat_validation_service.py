from __future__ import annotations

import pytest

from app.services.chat_validation_service import (
    FORBIDDEN_TERMS,
    REFUSAL_MESSAGES,
    BlockReason,
    ChatValidationService,
)


@pytest.fixture
def svc() -> ChatValidationService:
    return ChatValidationService()


def test_diagnosis_request_blocked(svc: ChatValidationService) -> None:
    assert svc.classify_intent("진단해줘") == "DIAGNOSIS_REQUEST"


def test_prescription_request_blocked(svc: ChatValidationService) -> None:
    assert svc.classify_intent("어떤 약 먹어야 해") == "PRESCRIPTION_REQUEST"


def test_dosage_change_blocked(svc: ChatValidationService) -> None:
    assert svc.classify_intent("약 끊어도 돼?") == "DOSAGE_CHANGE"


def test_emergency_blocked(svc: ChatValidationService) -> None:
    assert svc.classify_intent("응급실 가야 해?") == "EMERGENCY"


def test_self_harm_blocked(svc: ChatValidationService) -> None:
    assert svc.classify_intent("자살하고 싶어") == "SELF_HARM"


def test_normal_message_not_blocked(svc: ChatValidationService) -> None:
    assert svc.classify_intent("오늘 컨디션 좋아요") is None


def test_safety_filter_detects_forbidden_term(svc: ChatValidationService) -> None:
    assert svc.check_safety_expressions("제가 처방해드릴게요") == "처방해드릴"


def test_safety_filter_passes_neutral_text(svc: ChatValidationService) -> None:
    assert svc.check_safety_expressions("정기 검진이 권장됩니다") is None


def test_has_sources_with_items(svc: ChatValidationService) -> None:
    assert svc.has_sources([{"title": "루푸스 관리 가이드"}]) is True


def test_has_sources_empty(svc: ChatValidationService) -> None:
    assert svc.has_sources([]) is False


def test_get_refusal_message_for_each_reason(svc: ChatValidationService) -> None:
    for reason in BlockReason:
        msg = svc.get_refusal_message(reason)
        assert isinstance(msg, str)
        assert len(msg) > 0


def test_refusal_messages_no_forbidden_terms() -> None:
    for msg in REFUSAL_MESSAGES.values():
        for term in FORBIDDEN_TERMS:
            assert term not in msg, f"거부 문구에 금지 표현 포함: '{term}' in '{msg}'"
