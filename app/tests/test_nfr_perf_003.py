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
