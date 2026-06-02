from __future__ import annotations

import time

import jwt
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core import config as app_config
from app.core.rate_limit.config import get_tier

_redis_client: Redis | None = None


def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(app_config.REDIS_URL, decode_responses=True)
    return _redis_client


def _extract_user_id(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return str(user_id) if user_id is not None else None
    except jwt.exceptions.PyJWTError:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        user_id = _extract_user_id(request.headers.get("Authorization"))
        if user_id is None:
            return await call_next(request)

        tier = get_tier(request.method, request.url.path)
        window = int(time.time()) // 60
        key = f"rl:{user_id}:{tier.name}:{window}"

        try:
            redis = get_redis()
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)
            results = await pipe.execute()
            count = results[0]
        except Exception:
            return await call_next(request)

        if count > tier.limit:
            return JSONResponse(
                status_code=429,
                content={"code": "RATE_LIMIT_EXCEEDED", "message": "요청 횟수가 초과되었습니다."},
            )

        return await call_next(request)
