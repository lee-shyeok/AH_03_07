"""REQ-CHAT-004 강화 가드레일 단위 테스트."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chat_guardrail_enhanced import (
    _check_keywords,
    apply_enhanced_guardrail,
    handle_pre_save,
)

# ── 키워드 매칭 테스트 ────────────────────────────────────────────────────────


def test_clean_text_passes_keywords() -> None:
    result = _check_keywords("루푸스 환자는 햇빛을 피하는 것이 중요합니다.")
    assert result.status == "PASSED"


def test_autoimmune_drug_dosage_blocked() -> None:
    result = _check_keywords("메토트렉세이트 용량을 스스로 줄여도 될까요?")
    assert result.status == "BLOCKED"
    assert result.category == "AUTOIMMUNE_DRUG_DOSAGE"
    assert result.matched_keywords


def test_suicide_signal_blocked() -> None:
    result = _check_keywords("사라지고 싶은 생각이 들어요.")
    assert result.status == "BLOCKED"
    assert result.category == "SUICIDE_SIGNAL"
    # SEVERE_EMERGENCY post-LLM 검사 제거됨 — 응급은 pre-LLM classify_intent(EMERGENCY)에서 처리
    # 자살예방 번호 109 (구 1393에서 변경됨)
    assert "109" in (result.refusal_message or "")


def test_lab_interpretation_blocked() -> None:
    result = _check_keywords("내 CRP 수치 어때요?")
    assert result.status == "BLOCKED"
    assert result.category == "LAB_INTERPRETATION"


def test_score_evaluation_blocked() -> None:
    result = _check_keywords("DAS28 점수로 내 상태 알려줘.")
    assert result.status == "BLOCKED"
    assert result.category == "SCORE_EVALUATION"


def test_keyword_match_ignores_spaces() -> None:
    """공백 정규화 후 매칭해야 한다."""
    result = _check_keywords("스테로이드  줄여도 되나요?")
    assert result.status == "BLOCKED"
    assert result.category == "AUTOIMMUNE_DRUG_DOSAGE"


def test_matched_keywords_listed_in_result() -> None:
    result = _check_keywords("DMARD 끊어도 괜찮아요?")
    assert result.status == "BLOCKED"
    assert len(result.matched_keywords) >= 1


# ── Moderation API 통합 테스트 ────────────────────────────────────────────────


def _make_moderation_response(flagged: bool, categories: dict | None = None) -> SimpleNamespace:
    """OpenAI Moderation API 응답 Mock 생성.

    SimpleNamespace를 사용해 __dict__ 기반 순회가 올바르게 동작하도록 한다.
    """
    cat = SimpleNamespace(**(categories or {}))
    result = SimpleNamespace(flagged=flagged, categories=cat)
    return SimpleNamespace(results=[result])


@pytest.mark.asyncio
async def test_moderation_api_flagged_blocks() -> None:
    """Moderation API가 flagged=True이면 BLOCKED를 반환한다."""
    mock_resp = _make_moderation_response(flagged=True, categories={"violence": True})

    with patch("app.services.chat_guardrail_enhanced.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_client.moderations.create = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        result = await apply_enhanced_guardrail("일반적인 내용이지만 API가 탐지함")

    assert result.status == "BLOCKED"
    assert result.category == "MODERATION_API"
    assert "violence" in result.matched_keywords


@pytest.mark.asyncio
async def test_moderation_api_not_flagged_passes() -> None:
    """Moderation API flagged=False이고 키워드도 없으면 PASSED."""
    mock_resp = _make_moderation_response(flagged=False)

    with patch("app.services.chat_guardrail_enhanced.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_client.moderations.create = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        result = await apply_enhanced_guardrail("루푸스 환자의 일반적인 생활 관리 방법입니다.")

    assert result.status == "PASSED"


@pytest.mark.asyncio
async def test_keyword_match_skips_moderation_api() -> None:
    """1단계 키워드에서 차단되면 Moderation API를 호출하지 않는다."""
    # "가슴 통증"은 SEVERE_EMERGENCY 제거로 매칭 안 됨 → SUICIDE_SIGNAL 살아있는 키워드로 교체
    with patch("app.services.chat_guardrail_enhanced.AsyncOpenAI") as mock_cls:
        result = await apply_enhanced_guardrail("사라지고 싶은 생각이 들어요.")

    mock_cls.assert_not_called()
    assert result.status == "BLOCKED"
    assert result.category == "SUICIDE_SIGNAL"


# ── pre_save signal 핸들러 테스트 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_pre_save_skips_user_role() -> None:
    """USER 역할 메시지는 검사하지 않는다."""
    from app.models.chat_message import ChatMessage

    instance = MagicMock(spec=ChatMessage)
    instance.role = "USER"

    with patch("app.services.chat_guardrail_enhanced.apply_enhanced_guardrail") as mock_fn:
        await handle_pre_save(ChatMessage, instance, None, None)
        mock_fn.assert_not_called()


@pytest.mark.asyncio
async def test_handle_pre_save_skips_already_blocked() -> None:
    """이미 blocked_by_filter=True인 메시지는 재검사하지 않는다."""
    from app.models.chat_message import ChatMessage

    instance = MagicMock(spec=ChatMessage)
    instance.role = "ASSISTANT"
    instance.blocked_by_filter = True

    with patch("app.services.chat_guardrail_enhanced.apply_enhanced_guardrail") as mock_fn:
        await handle_pre_save(ChatMessage, instance, None, None)
        mock_fn.assert_not_called()


@pytest.mark.asyncio
async def test_handle_pre_save_sets_blocked_fields_on_detection() -> None:
    """차단 시 blocked_by_filter, block_reason, content가 올바르게 수정된다."""
    from app.models.chat_message import ChatMessage

    instance = MagicMock(spec=ChatMessage)
    instance.role = "ASSISTANT"
    instance.blocked_by_filter = False
    # "가슴 통증" SEVERE_EMERGENCY 제거로 더 이상 차단 안 됨 → SUICIDE_SIGNAL 살아있는 트리거로 교체
    instance.content = "사라지고 싶은 생각이 들어요."
    instance.id = 1
    instance.session_id = 42

    with patch("app.services.chat_guardrail_enhanced.log_guardrail_block") as mock_log:
        await handle_pre_save(ChatMessage, instance, None, None)

    assert instance.blocked_by_filter is True
    assert "SUICIDE_SIGNAL" in instance.block_reason
    assert "109" in instance.content  # SUICIDE_SIGNAL 거부 문구에 자살예방 109 포함
    mock_log.assert_called_once()
    _, kwargs = mock_log.call_args if mock_log.call_args.kwargs else (None, {})
    call_kwargs = mock_log.call_args.kwargs
    assert call_kwargs.get("category") == "SUICIDE_SIGNAL"


@pytest.mark.asyncio
async def test_handle_pre_save_passes_clean_assistant_message() -> None:
    """정상 ASSISTANT 메시지는 필드 수정 없이 통과한다."""
    from app.models.chat_message import ChatMessage

    mock_resp = _make_moderation_response(flagged=False)

    instance = MagicMock(spec=ChatMessage)
    instance.role = "ASSISTANT"
    instance.blocked_by_filter = False
    original_content = "자외선 차단제를 매일 사용하는 것이 중요합니다."
    instance.content = original_content

    with patch("app.services.chat_guardrail_enhanced.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_client.moderations.create = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        await handle_pre_save(ChatMessage, instance, None, None)

    assert instance.blocked_by_filter is False
    assert instance.content == original_content
