"""NFR-SAFE-004 — 제공 금지 기능 차단 정책.

관련 법령에 따라 제공이 금지된 8가지 기능을 탐지하고 차단한다.
차단 이력은 NFR-SAFE-003의 safety_filter_logs 테이블에 저장한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

REFUSAL_MESSAGE = "이 기능은 관련 법령에 따라 제공이 제한됩니다. 담당 의료진과 직접 상담하세요."

# blocked_reason(max_length=100) 제약: 전체 카테고리명 대신 약어 코드 사용
_CATEGORY_CODES: dict[str, str] = {
    "telemedicine_brokerage": "TMB",
    "doctor_matching": "DM",
    "prescription_handling": "PH",
    "drug_recommendation": "DR",
    "medical_judgment_interference": "MJI",
    "auto_emergency_report": "AER",
    "medical_institution_advertisement": "MIA",
    "referral_commission": "RC",
}

_RULESET: dict[str, list[str]] = {
    # 1. 의료법 비대면 진료 규정
    "telemedicine_brokerage": [
        "비대면 진료 예약",
        "원격 진료 예약",
        "화상 진료 연결",
        "비대면 진료 중개",
        "온라인 진료 예약",
    ],
    # 2. 의료법 제27조 제3항
    "doctor_matching": [
        "의사 매칭",
        "의사 소개",
        "의사 연결해",
        "의사 알선",
        "전문의 매칭",
        "담당의 연결",
    ],
    # 3. 처방전 요청·전송
    "prescription_handling": [
        "처방전 발급",
        "처방전 보내",
        "처방전 요청",
        "처방전 전송",
        "처방전 받아",
    ],
    # 4. 약사법 제24조
    "drug_recommendation": [
        "처방약 추천",
        "약 추천해줘",
        "어떤 약 먹어야",
        "약 변경해줘",
        "약 바꿔줘",
        "이 약 대신",
    ],
    # 5. 의료진 판단 개입
    "medical_judgment_interference": [
        "의사 판단 무시",
        "의사 말 무시",
        "처방 무시해도",
        "의사보다 내가",
        "의사 의견 틀렸",
    ],
    # 6. 응급의료법·통신법
    "auto_emergency_report": [
        "119 자동 신고",
        "119 자동 발신",
        "112 자동 신고",
        "자동으로 신고해",
        "대신 신고해줘",
    ],
    # 7. 의료법 제56조
    "medical_institution_advertisement": [
        "좋은 병원 추천",
        "병원 추천해줘",
        "병원 후기",
        "의원 광고",
        "병원 광고",
        "추천 병원",
    ],
    # 8. 의료법 제27조
    "referral_commission": [
        "소개비",
        "중개 수수료",
        "병원 소개 수수료",
        "의료기관 소개비",
        "진료 중개비",
    ],
}


@dataclass
class ProhibitedFeatureResult:
    is_blocked: bool
    matched_categories: list[str] = field(default_factory=list)
    refusal_message: str = ""


def apply_nfr_safe_004(text: str) -> ProhibitedFeatureResult:
    """NFR-SAFE-004 룰셋으로 텍스트를 검사한다."""
    matched: list[str] = []
    for category, patterns in _RULESET.items():
        for pattern in patterns:
            if pattern in text:
                matched.append(category)
                break

    if matched:
        return ProhibitedFeatureResult(
            is_blocked=True,
            matched_categories=matched,
            refusal_message=REFUSAL_MESSAGE,
        )
    return ProhibitedFeatureResult(is_blocked=False)


async def log_prohibited_block(
    *,
    user_id: int | None,
    target_type: str,
    target_id: str | None,
    matched_categories: list[str],
    original_text: str,
    filter_stage: str,
) -> None:
    """차단 이력을 safety_filter_logs 테이블에 저장한다."""
    from app.services.nfr_safe_003 import log_safety_block

    codes = [_CATEGORY_CODES[c] for c in matched_categories if c in _CATEGORY_CODES]
    await log_safety_block(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        matched_categories=codes,
        original_text=original_text,
        filter_stage=filter_stage,
    )


async def filter_and_log_004(
    text: str,
    *,
    user_id: int | None = None,
    target_type: str,
    target_id: str | None = None,
    filter_stage: str,
) -> ProhibitedFeatureResult:
    """필터 적용 후 차단 시 DB 로깅까지 수행하는 통합 함수."""
    result = apply_nfr_safe_004(text)
    if result.is_blocked:
        await log_prohibited_block(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            matched_categories=result.matched_categories,
            original_text=text,
            filter_stage=filter_stage,
        )
    return result
