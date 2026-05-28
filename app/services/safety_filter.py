"""NFR-SAFE-003 다단계 안전 표현 필터.

REQ-CHAT-007과 REQ-GUIDE-007이 공유하는 모듈.
의료법 §27 준수: 진단·처방·판독·추천·평가 표현 차단 후 정형 문구로 대체.
차단 이력은 NFR-COMPLI-004 감사 로그로 기록.
"""

import json
from dataclasses import dataclass, field

from app.core.logger import default_logger as logger

STANDARD_REPLACEMENT = "담당 의료진과 상담하시기 바랍니다."

# (a) 금지 키워드·동의어·우회 표현 사전 + (b) 의도 분류기 통합 룰셋
# 안전 표현("담당 의료진과 상담" 등)이 같은 텍스트에 있어도 금지 패턴이 우선한다.
_FORBIDDEN: dict[str, list[str]] = {
    "drug_stop": [
        "중단하세요",
        "끊으세요",
        "그만 드세요",
        "이제 안 드셔도",
        "복용을 멈추",
        "복용을 중단",
        "약을 끊",
    ],
    "drug_adjust": [
        "용량을 줄이",
        "용량을 늘리",
        "용량 조절",
        "약을 바꾸",
        "처방을 변경",
        "다른 약으로 바꾸",
        "약 변경",
    ],
    "diagnosis": [
        "진단됩니다",
        "확정됩니다",
        "확진",
        "진단이 확정",
    ],
    "lab_interpret": [
        "수치가 높습니다",
        "수치가 낮습니다",
        "결과가 정상입니다",
        "결과가 비정상",
        "검사 결과상",
    ],
    "assessment": [
        "위험합니다",
        "심각합니다",
        "악화되었습니다",
        "고위험입니다",
        "활성도 점수가 ",
    ],
    "recommend_treatment": [
        "이 약을 드세요",
        "치료를 받으세요",
        "치료를 시작하세요",
        "처방받으세요",
    ],
}


@dataclass
class SafetyFilterResult:
    is_blocked: bool
    matched_patterns: list[str] = field(default_factory=list)
    # is_blocked=True 이면 STANDARD_REPLACEMENT, False 이면 원본 텍스트
    filtered_text: str = ""


def apply_safety_filter(text: str) -> SafetyFilterResult:
    """(a)+(b) 금지 패턴 항상 스캔 → 매칭 시 (d) 정형 문구 대체."""
    matched: list[str] = []
    for category, patterns in _FORBIDDEN.items():
        for pattern in patterns:
            if pattern in text:
                matched.append(f"{category}:{pattern}")

    if matched:
        return SafetyFilterResult(
            is_blocked=True,
            matched_patterns=matched,
            filtered_text=STANDARD_REPLACEMENT,
        )
    return SafetyFilterResult(is_blocked=False, filtered_text=text)


def log_block_event(user_id: int, section: str, matched_patterns: list[str]) -> None:
    """(e) 차단 이력 감사 로그 (NFR-COMPLI-004)."""
    logger.warning(
        json.dumps(
            {
                "event": "nfr_safe_003_block",
                "user_id": user_id,
                "section": section,
                "matched_patterns": matched_patterns,
            }
        )
    )
