from __future__ import annotations

from enum import StrEnum


class BlockReason(StrEnum):
    NO_SOURCES = "NO_SOURCES"
    SAFETY_FILTER = "SAFETY_FILTER"
    INTENT_BLOCKED = "INTENT_BLOCKED"


FORBIDDEN_TERMS = [
    "진단해드립니다",
    "진단해 드립니다",
    "진단해드릴",
    "진단해 드릴",
    "진단해줄게",
    "처방해드립니다",
    "처방해 드립니다",
    "처방해드릴",
    "처방해 드릴",
    "처방해줄게",
    "약 조절",
    "비대면 진료",
    "의사 매칭",
]

BLOCKED_INTENT_KEYWORDS: dict[str, list[str]] = {
    "DIAGNOSIS_REQUEST": ["진단해줘", "무슨 병이야", "병명 알려줘", "진단해 주세요"],
    "PRESCRIPTION_REQUEST": ["약 처방", "약 추천", "어떤 약 먹어야", "약 추천해줘"],
    "DOSAGE_CHANGE": ["약 끊어도", "용량 바꿔", "약 줄여", "약 늘려"],
    "EMERGENCY": ["응급실", "지금 죽을 것 같", "심정지", "응급 상황"],
    "SELF_HARM": ["자살", "자해", "죽고 싶"],
}

REFUSAL_MESSAGES: dict[BlockReason, str] = {
    BlockReason.NO_SOURCES: ("관련된 신뢰할 만한 자료를 찾지 못했습니다. 정확한 정보는 의료진과 상의해 주세요."),
    BlockReason.SAFETY_FILTER: (
        "본 챗봇은 일반 정보 제공만 가능합니다. 구체적인 의학적 판단은 의료진과 상담해 주세요."
    ),
    BlockReason.INTENT_BLOCKED: ("이 질문은 의료진의 직접 상담이 필요합니다. 본 챗봇은 일반 정보 안내만 제공합니다."),
}


class ChatValidationService:
    def classify_intent(self, user_message: str) -> str | None:
        """3단계: 사용자 메시지 의도 분류. 차단 카테고리면 카테고리명, 아니면 None."""
        text = user_message.replace(" ", "")
        for category, keywords in BLOCKED_INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw.replace(" ", "") in text:
                    return category
        return None

    def check_safety_expressions(self, text: str) -> str | None:
        """2단계: 응답 텍스트의 금지 표현 검사. 발견 시 해당 단어, 아니면 None."""
        for term in FORBIDDEN_TERMS:
            if term in text:
                return term
        return None

    def has_sources(self, rag_sources: list) -> bool:
        """1단계: RAG 출처 존재 여부."""
        return bool(rag_sources)

    def get_refusal_message(self, reason: BlockReason) -> str:
        return REFUSAL_MESSAGES[reason]
