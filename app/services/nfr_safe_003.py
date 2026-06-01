"""NFR-SAFE-003 — 의료행위 차단 룰셋 및 DB 이력 저장.

의료법 §27 준수: 진단·처방·판독·추천·예후 표현 차단 후 안전 문구로 전환.
차단 이력은 safety_filter_logs 테이블에 저장한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SAFE_REPLACEMENT = "이 부분은 담당 의료진 또는 약사 상담이 필요합니다"

_RULESET: dict[str, list[str]] = {
    "diagnosis_presumption": [
        "로 보입니다",
        "으로 보입니다",
        "의심됩니다",
        "로 진단할 수 있습니다",
        "으로 진단할 수 있습니다",
        "인 것 같습니다",
        "일 가능성이 높습니다",
    ],
    "drug_modification": [
        "를 중단하세요",
        "을 중단하세요",
        "를 늘리세요",
        "을 늘리세요",
        "로 바꾸세요",
        "으로 바꾸세요",
        "를 줄이세요",
        "을 줄이세요",
        "복용을 중단",
        "복용을 늘",
        "용량을 조절",
    ],
    "lab_interpretation": [
        "수치가 위험합니다",
        "수치가 높습니다",
        "수치가 낮습니다",
        "정상입니다",
        "비정상입니다",
        "결과가 정상",
        "결과가 비정상",
    ],
    "treatment_recommendation": [
        "를 복용하세요",
        "을 복용하세요",
        "를 추천드립니다",
        "을 추천드립니다",
        "이 약을 드세요",
        "처방받으세요",
        "치료를 시작하세요",
    ],
    "prognosis_risk": [
        "% 확률",
        "향후",
        "할 가능성",
        "발병할 수 있습니다",
        "재발할 수 있습니다",
    ],
}

# 예후·위험도 카테고리는 수치+맥락 조합 패턴이므로 정규식으로 보완
_PROGNOSIS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\d+\s*%\s*확률"),
    re.compile(r"향후.{0,20}(할|될|발생|진행)\s*(가능성|수\s*있)"),
]


@dataclass
class SafetyFilterResult:
    is_blocked: bool
    matched_categories: list[str] = field(default_factory=list)
    filtered_text: str = ""


def apply_nfr_safe_003(text: str) -> SafetyFilterResult:
    """NFR-SAFE-003 룰셋으로 텍스트를 검사한다."""
    matched: list[str] = []

    for category, patterns in _RULESET.items():
        for pattern in patterns:
            if pattern in text:
                matched.append(category)
                break

    for regex in _PROGNOSIS_PATTERNS:
        if regex.search(text):
            if "prognosis_risk" not in matched:
                matched.append("prognosis_risk")
            break

    if matched:
        return SafetyFilterResult(
            is_blocked=True,
            matched_categories=matched,
            filtered_text=SAFE_REPLACEMENT,
        )
    return SafetyFilterResult(is_blocked=False, filtered_text=text)


async def log_safety_block(
    *,
    user_id: int | None,
    target_type: str,
    target_id: str | None,
    matched_categories: list[str],
    original_text: str,
    filter_stage: str,
) -> None:
    """차단 이력을 safety_filter_logs 테이블에 저장한다."""
    from app.models.safety_filter_log import SafetyFilterLog

    await SafetyFilterLog.create(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        blocked_reason=",".join(matched_categories),
        original_text=original_text,
        safe_replacement_text=SAFE_REPLACEMENT,
        filter_stage=filter_stage,
    )


async def filter_and_log(
    text: str,
    *,
    user_id: int | None = None,
    target_type: str,
    target_id: str | None = None,
    filter_stage: str,
) -> SafetyFilterResult:
    """필터 적용 후 차단 시 DB 로깅까지 수행하는 통합 함수."""
    result = apply_nfr_safe_003(text)
    if result.is_blocked:
        await log_safety_block(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            matched_categories=result.matched_categories,
            original_text=text,
            filter_stage=filter_stage,
        )
    return result
