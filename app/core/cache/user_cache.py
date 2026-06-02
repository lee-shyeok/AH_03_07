from __future__ import annotations

from app.core.cache.client import TTL_USER_PROFILE, cache_delete, cache_get_json, cache_set_json
from app.dtos.users import UserInfoResponse
from app.repositories.user_repository import UserRepository


def _user_cache_key(user_id: int) -> str:
    return f"cache:user:profile:{user_id}"


class UserCacheService:
    """사용자 프로필 Cache-Aside 서비스 (NFR-PERF-003).

    teammates가 GET /users/me 등에서 DB 직접 조회 대신 호출하면
    Redis 캐시를 먼저 확인하고 미스 시에만 DB를 조회한다.
    TTL: 600 s (10분).
    """

    @staticmethod
    async def get_cached_user_info(user_id: int) -> dict | None:
        """user_id로 프로필을 조회한다. 캐시 히트 시 DB를 건너뛴다."""
        key = _user_cache_key(user_id)
        cached = await cache_get_json(key)
        if cached is not None:
            return cached

        user = await UserRepository().get_user(user_id)
        if user is None:
            return None

        data = UserInfoResponse.model_validate(user).model_dump(mode="json")
        await cache_set_json(key, data, ttl=TTL_USER_PROFILE)
        return data

    @staticmethod
    async def invalidate(user_id: int) -> None:
        """유저 정보 변경 시 캐시를 무효화한다."""
        await cache_delete(_user_cache_key(user_id))
