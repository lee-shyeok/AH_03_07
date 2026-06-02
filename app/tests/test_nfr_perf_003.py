"""NFR-PERF-003 — Redis 캐시 단위 테스트."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

# ── cache client 헬퍼 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_set_and_get_json() -> None:
    """set 후 get이 동일한 딕셔너리를 반환한다."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=json.dumps({"foo": "bar"}))
    mock_redis.setex = AsyncMock()

    with patch("app.core.cache.client.get_cache", return_value=mock_redis):
        from app.core.cache.client import cache_get_json, cache_set_json

        await cache_set_json("test:key", {"foo": "bar"}, ttl=60)
        result = await cache_get_json("test:key")

    assert result == {"foo": "bar"}
    mock_redis.setex.assert_awaited_once_with("test:key", 60, json.dumps({"foo": "bar"}))


@pytest.mark.asyncio
async def test_cache_get_json_miss_returns_none() -> None:
    """캐시 미스(None) 시 None을 반환한다."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.core.cache.client.get_cache", return_value=mock_redis):
        from app.core.cache.client import cache_get_json

        result = await cache_get_json("test:missing")

    assert result is None


@pytest.mark.asyncio
async def test_cache_delete_calls_redis_delete() -> None:
    """cache_delete가 Redis delete를 호출한다."""
    mock_redis = AsyncMock()
    mock_redis.delete = AsyncMock()

    with patch("app.core.cache.client.get_cache", return_value=mock_redis):
        from app.core.cache.client import cache_delete

        await cache_delete("test:key")

    mock_redis.delete.assert_awaited_once_with("test:key")


# ── 약품 검색 캐시 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_drug_search_cache_hit_skips_http() -> None:
    """캐시 히트 시 외부 HTTP 호출을 하지 않는다."""
    cached_payload = {
        "query": "타이레놀",
        "total_count": 1,
        "drugs": [
            {
                "item_name": "타이레놀정500mg",
                "entp_name": None,
                "item_seq": None,
                "efcy_qesitm": None,
                "use_method_qesitm": None,
                "atpn_warn_qesitm": None,
                "atpn_qesitm": None,
                "intrc_qesitm": None,
                "se_qesitm": None,
                "deposit_method_qesitm": None,
                "item_image": None,
            }
        ],
    }

    from app.services.drug_info import DrugInfoService

    with (
        patch("app.services.drug_info.cache_get_json", return_value=cached_payload),
        patch("app.services.drug_info.cache_set_json") as mock_set,
        patch("httpx.AsyncClient") as mock_http,
    ):
        result = await DrugInfoService().search_drug("타이레놀", 5)

    mock_http.assert_not_called()
    mock_set.assert_not_called()
    assert result.query == "타이레놀"
    assert result.drugs[0].item_name == "타이레놀정500mg"


@pytest.mark.asyncio
async def test_drug_search_cache_miss_calls_http_and_stores() -> None:
    """캐시 미스 시 HTTP를 호출하고 결과를 캐시에 저장한다."""
    from unittest.mock import MagicMock

    api_response = {"body": {"items": [{"itemName": "타이레놀정500mg"}], "totalCount": 1}}

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=api_response)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    from app.services.drug_info import DrugInfoService

    with (
        patch("app.services.drug_info.cache_get_json", return_value=None),
        patch("app.services.drug_info.cache_set_json") as mock_set,
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        result = await DrugInfoService().search_drug("타이레놀", 5)

    mock_set.assert_awaited_once()
    key, payload = mock_set.call_args.args
    assert key == "cache:drug:search:타이레놀:5"
    assert mock_set.call_args.kwargs["ttl"] == 3600
    assert result.drugs[0].item_name == "타이레놀정500mg"


# ── 사용자 프로필 캐시 서비스 ──────────────────────────────────


@pytest.mark.asyncio
async def test_user_cache_hit_skips_db() -> None:
    """캐시 히트 시 DB 조회를 건너뛴다."""
    from app.core.cache.user_cache import UserCacheService

    cached = {"id": 1, "name": "테스터"}

    with (
        patch("app.core.cache.user_cache.cache_get_json", return_value=cached),
        patch("app.core.cache.user_cache.cache_set_json") as mock_set,
        patch("app.core.cache.user_cache.UserRepository") as mock_repo_cls,
    ):
        result = await UserCacheService.get_cached_user_info(user_id=1)

    mock_repo_cls.assert_not_called()
    mock_set.assert_not_called()
    assert result == cached


@pytest.mark.asyncio
async def test_user_cache_miss_queries_db_and_stores() -> None:
    """캐시 미스 시 DB를 조회하고 결과를 캐시에 저장한다."""
    from datetime import date, datetime
    from unittest.mock import MagicMock

    from app.core.cache.user_cache import UserCacheService

    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.name = "신규유저"
    mock_user.email = "new@example.com"
    mock_user.phone_number = "01099998888"
    mock_user.birthday = date(1995, 5, 15)
    mock_user.gender = "FEMALE"
    mock_user.created_at = datetime(2026, 1, 1)

    mock_repo = AsyncMock()
    mock_repo.get_user = AsyncMock(return_value=mock_user)

    with (
        patch("app.core.cache.user_cache.cache_get_json", return_value=None),
        patch("app.core.cache.user_cache.cache_set_json") as mock_set,
        patch("app.core.cache.user_cache.UserRepository", return_value=mock_repo),
    ):
        result = await UserCacheService.get_cached_user_info(user_id=2)

    mock_set.assert_awaited_once()
    assert mock_set.call_args.args[0] == "cache:user:profile:2"
    assert mock_set.call_args.kwargs["ttl"] == 600
    assert result is not None
    assert result["name"] == "신규유저"


@pytest.mark.asyncio
async def test_user_cache_miss_returns_none_when_user_not_found() -> None:
    """DB에 유저가 없으면 None을 반환한다."""
    from app.core.cache.user_cache import UserCacheService

    mock_repo = AsyncMock()
    mock_repo.get_user = AsyncMock(return_value=None)

    with (
        patch("app.core.cache.user_cache.cache_get_json", return_value=None),
        patch("app.core.cache.user_cache.cache_set_json") as mock_set,
        patch("app.core.cache.user_cache.UserRepository", return_value=mock_repo),
    ):
        result = await UserCacheService.get_cached_user_info(user_id=999)

    mock_set.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_user_cache_invalidate_deletes_key() -> None:
    """invalidate 호출 시 해당 유저 캐시 키를 삭제한다."""
    from app.core.cache.user_cache import UserCacheService

    with patch("app.core.cache.user_cache.cache_delete") as mock_del:
        await UserCacheService.invalidate(user_id=3)

    mock_del.assert_awaited_once_with("cache:user:profile:3")


# ── 가이드 상세 캐시 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_guide_cache_hit_skips_repo() -> None:
    """캐시 히트 시 레포지토리 조회를 건너뛴다."""
    from uuid import UUID

    from app.services.health_guides import HealthGuideService

    guide_id = UUID("11111111-1111-1111-1111-111111111111")
    cached_guide = {
        "id": str(guide_id),
        "guide_type": "GENERAL",
        "status": "COMPLETED",
        "user_question": "두통이 심해요",
        "guide_content": "충분한 수분 섭취를 권장합니다.",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }

    service = HealthGuideService.__new__(HealthGuideService)
    service.repo = AsyncMock()

    with (
        patch("app.services.health_guides.cache_get_json", return_value=cached_guide),
        patch("app.services.health_guides.cache_set_json") as mock_set,
    ):
        result = await service.get_guide_by_id(guide_id)

    service.repo.get_by_id.assert_not_called()
    mock_set.assert_not_called()
    assert result is not None
    assert result.guide_content == "충분한 수분 섭취를 권장합니다."


@pytest.mark.asyncio
async def test_guide_cache_miss_queries_repo_and_stores() -> None:
    """캐시 미스 시 레포지토리를 조회하고 결과를 캐시에 저장한다."""
    from datetime import datetime
    from unittest.mock import MagicMock
    from uuid import uuid4

    from app.services.health_guides import HealthGuideService

    guide_id = uuid4()
    mock_guide = MagicMock()
    mock_guide.id = guide_id
    mock_guide.guide_type = "GENERAL"
    mock_guide.status = "COMPLETED"
    mock_guide.user_question = "두통이 심해요"
    mock_guide.guide_content = "충분한 수분 섭취를 권장합니다."
    mock_guide.created_at = datetime(2026, 1, 1)
    mock_guide.updated_at = datetime(2026, 1, 1)

    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_guide)

    service = HealthGuideService.__new__(HealthGuideService)
    service.repo = mock_repo

    with (
        patch("app.services.health_guides.cache_get_json", return_value=None),
        patch("app.services.health_guides.cache_set_json") as mock_set,
    ):
        result = await service.get_guide_by_id(guide_id)

    mock_set.assert_awaited_once()
    assert mock_set.call_args.args[0] == f"cache:guide:detail:{guide_id}"
    assert mock_set.call_args.kwargs["ttl"] == 1800
    assert result is not None
    assert result.guide_content == "충분한 수분 섭취를 권장합니다."


@pytest.mark.asyncio
async def test_guide_cache_miss_returns_none_when_not_found() -> None:
    """레포지토리에 가이드가 없으면 None을 반환한다."""
    from uuid import uuid4

    from app.services.health_guides import HealthGuideService

    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(return_value=None)

    service = HealthGuideService.__new__(HealthGuideService)
    service.repo = mock_repo

    with (
        patch("app.services.health_guides.cache_get_json", return_value=None),
        patch("app.services.health_guides.cache_set_json") as mock_set,
    ):
        result = await service.get_guide_by_id(uuid4())

    mock_set.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_guide_cache_invalidated_on_cache_invalidate_call() -> None:
    """invalidate_guide_cache 호출 시 해당 가이드 캐시 키를 삭제한다."""
    from uuid import uuid4

    from app.services.health_guides import HealthGuideService

    guide_id = uuid4()
    service = HealthGuideService.__new__(HealthGuideService)

    with patch("app.services.health_guides.cache_delete") as mock_del:
        await service.invalidate_guide_cache(guide_id)

    mock_del.assert_awaited_once_with(f"cache:guide:detail:{guide_id}")
