from __future__ import annotations

from enum import StrEnum


class BlockReason(StrEnum):
    NO_SOURCES = "NO_SOURCES"
    SAFETY_FILTER = "SAFETY_FILTER"
    INTENT_BLOCKED = "INTENT_BLOCKED"
    SELF_HARM = "SELF_HARM"
    EMERGENCY = "EMERGENCY"


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

# 우선순위 순서 유지: SELF_HARM → EMERGENCY → 나머지 의도
BLOCKED_INTENT_KEYWORDS: dict[str, list[str]] = {
    "SELF_HARM": [
        "죽고싶",
        "죽고 싶",
        "자살",
        "자해",
        "사라지고 싶",
        "없어지고 싶",
        "목숨",
        "살기 싫",
        "살고 싶지 않",
    ],
    "EMERGENCY": [
        "호흡곤란",
        "숨이 안",
        "숨쉬기 힘",
        "숨 쉬기 힘",
        "흉통",
        "가슴 통증",
        "가슴이 조이",
        "의식이 없",
        "의식 저하",
        "경련",
        "쓰러",
        "심한 출혈",
        "마비",
        "응급실",
        "지금 죽을 것 같",
        "심정지",
        "응급 상황",
    ],
    "DIAGNOSIS_REQUEST": ["진단해줘", "무슨 병이야", "병명 알려줘", "진단해 주세요"],
    "PRESCRIPTION_REQUEST": ["약 처방", "약 추천", "어떤 약 먹어야", "약 추천해줘"],
    "DOSAGE_CHANGE": ["약 끊어도", "용량 바꿔", "약 줄여", "약 늘려"],
}

REFUSAL_MESSAGES: dict[BlockReason, str] = {
    BlockReason.NO_SOURCES: ("관련된 신뢰할 만한 자료를 찾지 못했습니다. 정확한 정보는 의료진과 상의해 주세요."),
    BlockReason.SAFETY_FILTER: (
        "본 챗봇은 일반 정보 제공만 가능합니다. 구체적인 의학적 판단은 의료진과 상담해 주세요."
    ),
    BlockReason.INTENT_BLOCKED: ("이 질문은 의료진의 직접 상담이 필요합니다. 본 챗봇은 일반 정보 안내만 제공합니다."),
    BlockReason.SELF_HARM: (
        "많이 힘드셨겠어요. 혼자 견디지 않으셔도 됩니다. "
        "자살예방 상담전화 109번으로 전화하시면 24시간 전문 상담을 받으실 수 있어요. "
        "정신건강 상담은 1577-0199도 있습니다. "
        "지금 위급한 상황이라면 119로 바로 연락해 주세요."
    ),
    BlockReason.EMERGENCY: (
        "호흡곤란·흉통 등은 응급 상황일 수 있습니다. "
        "지금 바로 119에 연락하거나 가까운 응급실을 방문해 주세요. "
        "본 챗봇은 응급 처치를 대신할 수 없습니다."
    ),
}

# 호흡곤란 조합 규칙 토큰 (text는 공백 제거 상태이므로 토큰도 공백 없이 정의)
# "숨바꼭질/숨다" 오탐 방지: "숨쉬/숨이/숨을/호흡" 으로 한정
_BREATHING_TOKENS: tuple[str, ...] = ("숨쉬", "숨이", "숨을", "호흡")
_DISTRESS_TOKENS: tuple[str, ...] = ("힘들", "곤란", "막혀", "막힌", "안쉬", "못쉬", "어려", "안돼")
# 흉통 조합 — 의료 안전상 과차단 허용
_CHEST_PAIN_TOKENS: tuple[str, ...] = ("조이", "답답", "통증", "아파", "아프")

# 복용량 변경 조합 규칙 토큰 (공백 제거 형태로 정의)
_DOSE_NOUN_TOKENS: tuple[str, ...] = ("용량", "복용량", "투여량", "약")
_DOSE_CHANGE_TOKENS: tuple[str, ...] = (
    "줄여",
    "줄이",
    "늘려",
    "늘리",
    "낮춰",
    "낮추",
    "올려",
    "올리",
    "끊",
    "중단",
    "그만먹",
    "그만드",
    "감량",
    "증량",
    "반으로",
    "두배",
    "바꿔",
    "변경",
    "안먹어도",
    "안드셔도",
)


class ChatValidationService:
    def classify_intent(self, user_message: str) -> str | None:
        """사용자 메시지 의도 분류. 우선순위: SELF_HARM → EMERGENCY → 기타 의도."""
        text = user_message.replace(" ", "")

        # 1순위: SELF_HARM literal
        for kw in BLOCKED_INTENT_KEYWORDS["SELF_HARM"]:
            if kw.replace(" ", "") in text:
                return "SELF_HARM"

        # 2순위: EMERGENCY 조합 규칙 (부사 삽입 구어체 대응)
        if any(b in text for b in _BREATHING_TOKENS) and any(d in text for d in _DISTRESS_TOKENS):
            return "EMERGENCY"
        if "가슴" in text and any(k in text for k in _CHEST_PAIN_TOKENS):
            return "EMERGENCY"

        # 2순위: EMERGENCY literal (조합 규칙 미탐지 보완)
        for kw in BLOCKED_INTENT_KEYWORDS["EMERGENCY"]:
            if kw.replace(" ", "") in text:
                return "EMERGENCY"

        # 3순위~: DIAGNOSIS_REQUEST / PRESCRIPTION_REQUEST literal
        for category in ("DIAGNOSIS_REQUEST", "PRESCRIPTION_REQUEST"):
            for kw in BLOCKED_INTENT_KEYWORDS[category]:
                if kw.replace(" ", "") in text:
                    return category

        # DOSAGE_CHANGE 조합 규칙 (구어체·약물명 삽입 변형 대응)
        if any(n in text for n in _DOSE_NOUN_TOKENS) and any(c in text for c in _DOSE_CHANGE_TOKENS):
            return "DOSAGE_CHANGE"

        # DOSAGE_CHANGE literal (조합 규칙 미탐지 보완)
        for kw in BLOCKED_INTENT_KEYWORDS["DOSAGE_CHANGE"]:
            if kw.replace(" ", "") in text:
                return "DOSAGE_CHANGE"

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
