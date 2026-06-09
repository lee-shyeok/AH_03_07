"""NFR-SAFE-002 RAG 지식베이스 출처 검증 게이트.

자가면역 RAG 지식베이스에 적재되는 자료를 공신력 있는 출처로 제한한다.
KnowledgeDocument 저장 전 pre_save signal로 자동 실행된다.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from tortoise.signals import pre_save

from app.core.logger import default_logger as logger

TRUSTED_ORGANIZATIONS: frozenset[str] = frozenset(
    {
        "대한류마티스학회",
        "EULAR",
        "ACR",
        "식약처",
        "보건복지부",
        "질병관리청",
    }
)

ORGANIZATION_URLS: dict[str, str] = {
    "대한류마티스학회": "https://www.rheum.or.kr",
    "EULAR": "https://www.eular.org",
    "ACR": "https://rheumatology.org",
    "식약처": "https://nedrug.mfds.go.kr",
    "보건복지부": "https://www.mohw.go.kr",
    "질병관리청": "https://www.kdca.go.kr",
}


def get_source_url(org: str) -> str | None:
    return ORGANIZATION_URLS.get(org)


MAX_YEARS_OLD = 5


@dataclass
class SourceValidationResult:
    status: Literal["PASSED", "WARNING", "BLOCKED"]
    reason: str = ""


def validate_source(source_organization: str, published_year: int) -> SourceValidationResult:
    """출처 조직과 발간연도로 적재 가능 여부를 판정한다."""
    if source_organization not in TRUSTED_ORGANIZATIONS:
        return SourceValidationResult(
            status="BLOCKED",
            reason=f"비공인 출처: '{source_organization}'. 허용 출처: {sorted(TRUSTED_ORGANIZATIONS)}",
        )

    current_year = datetime.now().year
    age = current_year - published_year
    if age > MAX_YEARS_OLD:
        return SourceValidationResult(
            status="WARNING",
            reason=f"발간연도 {published_year}은 {age}년 전 자료입니다 (권장: {MAX_YEARS_OLD}년 이내).",
        )

    return SourceValidationResult(status="PASSED")


def log_source_warning(source_organization: str, published_year: int, reason: str) -> None:
    """오래된 공인 출처 자료 적재 시 감사 로그 기록 (NFR-COMPLI-004)."""
    logger.warning(
        json.dumps(
            {
                "event": "nfr_safe_002_warning",
                "source_organization": source_organization,
                "published_year": published_year,
                "reason": reason,
            },
            ensure_ascii=False,
        )
    )


def log_block_event(source_organization: str, published_year: int, reason: str) -> None:
    """비공인 출처 차단 감사 로그 기록 (NFR-COMPLI-004)."""
    logger.warning(
        json.dumps(
            {
                "event": "nfr_safe_002_blocked",
                "source_organization": source_organization,
                "published_year": published_year,
                "reason": reason,
            },
            ensure_ascii=False,
        )
    )


async def handle_pre_save(sender, instance, using_db, update_fields) -> None:  # type: ignore[no-untyped-def]
    """KnowledgeDocument pre_save 핸들러. 테스트에서 직접 호출 가능."""
    result = validate_source(instance.source_organization, instance.published_year)
    if result.status == "BLOCKED":
        log_block_event(instance.source_organization, instance.published_year, result.reason)
        raise ValueError(result.reason)
    if result.status == "WARNING":
        log_source_warning(instance.source_organization, instance.published_year, result.reason)


def _register_signals() -> None:
    """KnowledgeDocument pre_save signal 등록. main.py import 시 자동 호출된다."""
    from app.models.knowledge import KnowledgeDocument

    pre_save(KnowledgeDocument)(handle_pre_save)


_register_signals()
