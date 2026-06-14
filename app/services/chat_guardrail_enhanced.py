"""REQ-CHAT-004 챗봇 응답 가드레일 고도화.

기존 chat_validation_service.py(허승혜)를 수정하지 않고 별도 레이어로 추가한다.
ChatMessage(ASSISTANT) pre_save signal로 자동 실행된다.

검증 순서:
  1단계 — 한국 의료 특화 키워드 매칭 (동기, 비용 없음)
  2단계 — OpenAI Moderation API (키워드 미탐지 시 호출)

차단 시:
  - instance.blocked_by_filter = True
  - instance.block_reason = "ENHANCED_GUARDRAIL:{카테고리}"
  - instance.content = 카테고리별 정형 안내 문구 (원문 대체)
"""

import json
from dataclasses import dataclass, field
from typing import Literal

from openai import AsyncOpenAI
from tortoise.signals import pre_save

from app.core import config
from app.core.logger import default_logger as logger

# ── 한국 의료 특화 키워드 (chat_validation_service.py 미포함 항목) ───────────

_ENHANCED_KEYWORDS: dict[str, list[str]] = {
    "AUTOIMMUNE_DRUG_DOSAGE": [
        "메토트렉세이트 용량",
        "스테로이드 줄여",
        "DMARD 끊어",
        "프레드니솔론 양",
        "하이드록시클로로퀸 줄",
        "면역억제제 끊",
        "생물학적제제 중단",
        "류마티스 약 바꿔",
    ],
    # SEVERE_EMERGENCY 삭제: 응급은 pre-LLM classify_intent(EMERGENCY)에서 처리됨.
    # LLM이 루푸스 증상 등 정보성 응답에 "호흡곤란", "뇌졸중" 단어를 포함할 수 있어 오탐.
    "SUICIDE_SIGNAL": [
        "사라지고 싶",
        "끝내고 싶",
        "더는 못 살",
        "죽고 싶다고 생각",
        "스스로 목숨",
        "삶을 끝내",
    ],
    "LAB_INTERPRETATION": [
        "검사 결과 어때",
        "수치 어때",
        "위험한 수치",
        "정상 범위야",
        "내 CRP",
        "내 ESR",
        "항핵항체 결과",
    ],
    "SCORE_EVALUATION": [
        "활성도 점수",
        "내 상태 점수",
        "병이 심해졌",
        "악화됐는지",
        "DAS28",
        "SLEDAI",
    ],
}

# ── 카테고리별 정형 안내 문구 ────────────────────────────────────────────────

_REFUSAL_MESSAGES: dict[str, str] = {
    "AUTOIMMUNE_DRUG_DOSAGE": (
        "약물 용량 조절은 반드시 담당 류마티스 전문의와 상담하세요. "
        "임의로 약을 줄이거나 끊으면 질환이 급격히 악화될 수 있습니다."
    ),
    "SUICIDE_SIGNAL": (
        "자살예방 상담전화 109번으로 전화하시면 24시간 전문 상담을 받으실 수 있어요. "
        "정신건강 상담은 1577-0199도 있습니다. "
        "지금 위급한 상황이라면 119로 바로 연락해 주세요."
    ),
    "LAB_INTERPRETATION": "검사 결과 해석은 담당 의료진과 상담하시기 바랍니다.",
    "SCORE_EVALUATION": "질환 활성도 평가는 담당 의료진과 상담하시기 바랍니다.",
    "MODERATION_API": ("본 챗봇은 일반 정보 제공만 가능합니다. 구체적인 의학적 판단은 담당 의료진과 상담해 주세요."),
}


# ── 결과 타입 ────────────────────────────────────────────────────────────────


@dataclass
class EnhancedGuardrailResult:
    status: Literal["PASSED", "BLOCKED"]
    category: str | None = None
    matched_keywords: list[str] = field(default_factory=list)
    refusal_message: str | None = None


# ── 핵심 검증 함수 ───────────────────────────────────────────────────────────


def _check_keywords(text: str) -> EnhancedGuardrailResult:
    """1단계: 한국 의료 특화 키워드 매칭."""
    normalized = text.replace(" ", "")
    for category, keywords in _ENHANCED_KEYWORDS.items():
        matched = [kw for kw in keywords if kw.replace(" ", "") in normalized]
        if matched:
            return EnhancedGuardrailResult(
                status="BLOCKED",
                category=category,
                matched_keywords=matched,
                refusal_message=_REFUSAL_MESSAGES[category],
            )
    return EnhancedGuardrailResult(status="PASSED")


async def _check_moderation_api(text: str) -> EnhancedGuardrailResult:
    """2단계: OpenAI Moderation API 호출. API 오류 시 통과 처리."""
    try:
        openai = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        resp = await openai.moderations.create(input=text)
        result = resp.results[0]
        if result.flagged:
            flagged_categories = [cat for cat, flagged in result.categories.__dict__.items() if flagged]
            return EnhancedGuardrailResult(
                status="BLOCKED",
                category="MODERATION_API",
                matched_keywords=flagged_categories,
                refusal_message=_REFUSAL_MESSAGES["MODERATION_API"],
            )
    except Exception:
        logger.warning("OpenAI Moderation API unavailable — skipping 2nd-stage guardrail")
    return EnhancedGuardrailResult(status="PASSED")


async def apply_enhanced_guardrail(text: str) -> EnhancedGuardrailResult:
    """한국 의료 키워드(1단계) → Moderation API(2단계) 순서로 검증한다."""
    keyword_result = _check_keywords(text)
    if keyword_result.status == "BLOCKED":
        return keyword_result
    return await _check_moderation_api(text)


# ── 감사 로그 ────────────────────────────────────────────────────────────────


def log_guardrail_block(
    message_id: object,
    session_id: object,
    category: str,
    matched_keywords: list[str],
) -> None:
    """가드레일 차단 상세 감사 로그 (REQ-CHAT-004 / NFR-COMPLI-004)."""
    logger.warning(
        json.dumps(
            {
                "event": "req_chat_004_guardrail_blocked",
                "message_id": str(message_id),
                "session_id": str(session_id),
                "category": category,
                "matched_keywords": matched_keywords,
            },
            ensure_ascii=False,
        )
    )


# ── pre_save signal 핸들러 ───────────────────────────────────────────────────


async def handle_pre_save(sender, instance, using_db, update_fields) -> None:  # type: ignore[no-untyped-def]
    """ChatMessage pre_save 핸들러. 테스트에서 직접 호출 가능.

    ASSISTANT 메시지만 검사한다. 이미 차단된 메시지는 재검사하지 않는다.
    차단 시 ValueError 대신 instance 필드를 수정하여 저장은 허용한다
    (기존 blocked_by_filter 아키텍처와 일관성 유지).
    """
    if instance.role != "ASSISTANT":
        return
    if instance.blocked_by_filter:
        return

    result = await apply_enhanced_guardrail(instance.content)
    if result.status == "BLOCKED":
        log_guardrail_block(
            message_id=instance.id,
            session_id=getattr(instance, "session_id", None),
            category=result.category or "UNKNOWN",
            matched_keywords=result.matched_keywords,
        )
        instance.blocked_by_filter = True
        instance.block_reason = f"ENHANCED_GUARDRAIL:{result.category}"
        instance.content = result.refusal_message or _REFUSAL_MESSAGES["MODERATION_API"]


def _register_signals() -> None:
    """ChatMessage pre_save signal 등록. main.py import 시 자동 호출된다."""
    from app.models.chat_message import ChatMessage

    pre_save(ChatMessage)(handle_pre_save)


_register_signals()
