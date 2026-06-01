"""NFR-SAFE-002 출처 검증 단위 테스트."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.knowledge_source_validator import (
    MAX_YEARS_OLD,
    validate_source,
)

_CURRENT_YEAR = datetime.now().year


def test_trusted_org_recent_year_passes() -> None:
    result = validate_source("EULAR", _CURRENT_YEAR - 2)
    assert result.status == "PASSED"


def test_trusted_org_boundary_year_passes() -> None:
    result = validate_source("ACR", _CURRENT_YEAR - MAX_YEARS_OLD)
    assert result.status == "PASSED"


def test_trusted_org_outdated_returns_warning() -> None:
    result = validate_source("대한류마티스학회", _CURRENT_YEAR - (MAX_YEARS_OLD + 1))
    assert result.status == "WARNING"
    assert "년 전" in result.reason


def test_untrusted_org_returns_blocked() -> None:
    result = validate_source("네이버블로그", _CURRENT_YEAR)
    assert result.status == "BLOCKED"
    assert "비공인 출처" in result.reason


def test_untrusted_org_recent_year_still_blocked() -> None:
    result = validate_source("유튜브채널", _CURRENT_YEAR)
    assert result.status == "BLOCKED"


def test_case_sensitive_matching_blocks_lowercase() -> None:
    """허용 출처는 정확한 표기로만 통과해야 한다."""
    result = validate_source("eular", _CURRENT_YEAR)
    assert result.status == "BLOCKED"


def test_all_trusted_organizations_pass() -> None:
    from app.services.knowledge_source_validator import TRUSTED_ORGANIZATIONS

    for org in TRUSTED_ORGANIZATIONS:
        result = validate_source(org, _CURRENT_YEAR)
        assert result.status == "PASSED", f"{org} should pass"


@pytest.mark.asyncio
async def test_pre_save_signal_blocks_untrusted_org() -> None:
    """handle_pre_save가 비공인 출처 인스턴스에 ValueError를 발생시키는지 검증."""
    from app.models.knowledge import KnowledgeDocument
    from app.services.knowledge_source_validator import handle_pre_save

    instance = MagicMock(spec=KnowledgeDocument)
    instance.source_organization = "카카오뷰"
    instance.published_year = _CURRENT_YEAR

    with patch("app.services.knowledge_source_validator.log_block_event") as mock_log:
        with pytest.raises(ValueError, match="비공인 출처"):
            await handle_pre_save(KnowledgeDocument, instance, None, None)
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_pre_save_signal_warns_outdated_trusted_org() -> None:
    """handle_pre_save가 오래된 공인 출처에 WARNING 로그를 남기는지 검증."""
    from app.models.knowledge import KnowledgeDocument
    from app.services.knowledge_source_validator import handle_pre_save

    instance = MagicMock(spec=KnowledgeDocument)
    instance.source_organization = "식약처"
    instance.published_year = _CURRENT_YEAR - (MAX_YEARS_OLD + 2)

    with patch("app.services.knowledge_source_validator.log_source_warning") as mock_warn:
        await handle_pre_save(KnowledgeDocument, instance, None, None)
        mock_warn.assert_called_once()
