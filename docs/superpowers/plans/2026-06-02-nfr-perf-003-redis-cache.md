# NFR-PERF-003 Redis 캐시 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cache-Aside 패턴으로 세 엔드포인트(약품 검색·사용자 프로필·가이드 상세)의 Redis 캐시를 구현해 DB/외부 API 중복 호출을 줄인다.

**Architecture:** `app/core/cache/` 패키지에 Redis 클라이언트 헬퍼를 두고, 약품 검색과 가이드 상세는 서비스 레이어에서 Cache-Aside를 직접 적용한다. 사용자 프로필은 원본 `user_routers.py`(Meoyoug 작성, 수정 금지)를 건드리지 않고 `app/core/cache/user_cache_router.py`에 새 라우터를 만들어 `app/main.py`에 먼저 등록해 라우트 우선순위로 오버라이드한다.

**Tech Stack:** FastAPI, redis-py asyncio (`redis.asyncio.Redis`), `redis>=4.5.2` (이미 설치됨), pytest + `unittest.mock`

---

## 수정 금지 파일 정리

| 파일 | 작성자 | 조치 |
|------|-------|------|
| `app/apis/v1/user_routers.py` | Meoyoug | 수정 금지 — 새 라우터로 오버라이드 |
| `app/apis/v1/__init__.py` | shhur310 | 수정 금지 — main.py에서 직접 등록 |
| `app/dependencies/security.py` | Meoyoug | 수정 금지 — 임포트만 사용 가능 |
| `app/repositories/user_repository.py` | Meoyoug | 수정 금지 — 임포트만 사용 가능 |
| `app/services/jwt.py` | S_hyeok | 수정 금지 — 임포트만 사용 가능 |

---

## 캐시 키 설계

| 대상 | 키 패턴 | TTL |
|------|--------|-----|
| 약품 검색 | `cache:drug:search:{drug_name}:{num_of_rows}` | 3600 s |
| 사용자 프로필 | `cache:user:profile:{user_id}` | 600 s |
| 가이드 상세 | `cache:guide:detail:{guide_id}` | 1800 s |

---

## 파일 구조

```
app/core/cache/
  __init__.py          (새 파일)
  client.py            (새 파일) — Redis 클라이언트 싱글턴 + 헬퍼
  user_cache_router.py (새 파일) — GET /users/me 캐시 오버라이드 라우터

app/services/
  drug_info.py         (수정) — search_drug에 cache-aside 추가
  health_guides.py     (수정) — get_guide_by_id 추가, 캐시 적용, update_result에 무효화

app/apis/v1/
  health_guide_routers.py (수정) — GET /{guide_id} 엔드포인트 추가

app/main.py            (수정) — user_cache_router·health_guide_router 등록

app/tests/
  test_nfr_perf_003.py (새 파일) — 캐시 동작 단위 테스트
```

---

## Task 1: develop 브랜치에서 feature/nfr-perf-003 생성

**Files:**
- (없음 — git 명령만)

- [ ] **Step 1: develop 체크아웃 후 브랜치 생성**

```bash
git fetch origin
git checkout develop
git checkout -b feature/nfr-perf-003
```

- [ ] **Step 2: 브랜치 확인**

```bash
git status
```

Expected output:
```
On branch feature/nfr-perf-003
nothing to commit, working tree clean
```

---

## Task 2: `app/core/cache/client.py` — Redis 클라이언트 + 헬퍼

**Files:**
- Create: `app/core/cache/__init__.py`
- Create: `app/core/cache/client.py`

- [ ] **Step 1: 테스트 작성 (client 헬퍼 동작 확인)**

`app/tests/test_nfr_perf_003.py` 파일 생성:

```python
"""NFR-PERF-003 — Redis 캐시 단위 테스트."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache.client import cache_delete, cache_get_json, cache_set_json, get_cache


# ── 헬퍼 함수 테스트 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_set_and_get_json() -> None:
    """set 후 get이 동일한 딕셔너리를 반환한다."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=json.dumps({"foo": "bar"}))
    mock_redis.setex = AsyncMock()

    with patch("app.core.cache.client.get_cache", return_value=mock_redis):
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
        result = await cache_get_json("test:missing")

    assert result is None


@pytest.mark.asyncio
async def test_cache_delete_calls_redis_delete() -> None:
    """cache_delete가 Redis delete를 호출한다."""
    mock_redis = AsyncMock()
    mock_redis.delete = AsyncMock()

    with patch("app.core.cache.client.get_cache", return_value=mock_redis):
        await cache_delete("test:key")

    mock_redis.delete.assert_awaited_once_with("test:key")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'app.core.cache'`

- [ ] **Step 3: `app/core/cache/__init__.py` 생성**

```python
```
(빈 파일)

- [ ] **Step 4: `app/core/cache/client.py` 구현**

```python
from __future__ import annotations

import json

from redis.asyncio import Redis

from app.core import config as app_config

_cache_client: Redis | None = None

# TTL 상수 (초)
TTL_DRUG_SEARCH = 3600   # 1시간
TTL_USER_PROFILE = 600   # 10분
TTL_GUIDE_DETAIL = 1800  # 30분


def get_cache() -> Redis:
    global _cache_client
    if _cache_client is None:
        _cache_client = Redis.from_url(app_config.REDIS_URL, decode_responses=True)
    return _cache_client


async def cache_get_json(key: str) -> dict | None:
    redis = get_cache()
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set_json(key: str, value: dict, ttl: int) -> None:
    redis = get_cache()
    await redis.setex(key, ttl, json.dumps(value))


async def cache_delete(key: str) -> None:
    redis = get_cache()
    await redis.delete(key)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_cache_set_and_get_json app/tests/test_nfr_perf_003.py::test_cache_get_json_miss_returns_none app/tests/test_nfr_perf_003.py::test_cache_delete_calls_redis_delete -v
```

Expected: 3 PASSED

- [ ] **Step 6: 커밋**

```bash
git add app/core/cache/ app/tests/test_nfr_perf_003.py
git commit -m "feat: NFR-PERF-003 cache client — get/set/delete JSON 헬퍼 + TTL 상수"
```

---

## Task 3: 약품 검색 캐시 (`GET /api/v1/drug-info/search`)

**Files:**
- Modify: `app/services/drug_info.py`
- Modify (append): `app/tests/test_nfr_perf_003.py`

캐시 키: `cache:drug:search:{drug_name}:{num_of_rows}`, TTL 3600 s

- [ ] **Step 1: 약품 캐시 테스트 추가**

`app/tests/test_nfr_perf_003.py` 끝에 추가:

```python
# ── 약품 검색 캐시 ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_drug_search_cache_hit_skips_http() -> None:
    """캐시 히트 시 외부 HTTP 호출을 하지 않는다."""
    cached_payload = {
        "query": "타이레놀",
        "total_count": 1,
        "drugs": [{"item_name": "타이레놀정500mg", "entp_name": None, "item_seq": None,
                   "efcy_qesitm": None, "use_method_qesitm": None, "atpn_warn_qesitm": None,
                   "atpn_qesitm": None, "intrc_qesitm": None, "se_qesitm": None,
                   "deposit_method_qesitm": None, "item_image": None}],
    }

    with patch("app.services.drug_info.cache_get_json", return_value=cached_payload), \
         patch("app.services.drug_info.cache_set_json") as mock_set, \
         patch("httpx.AsyncClient") as mock_http:
        from app.services.drug_info import DrugInfoService
        service = DrugInfoService()
        result = await service.search_drug("타이레놀", 5)

    mock_http.assert_not_called()
    mock_set.assert_not_called()
    assert result.query == "타이레놀"
    assert result.drugs[0].item_name == "타이레놀정500mg"


@pytest.mark.asyncio
async def test_drug_search_cache_miss_calls_http_and_stores() -> None:
    """캐시 미스 시 HTTP를 호출하고 결과를 캐시에 저장한다."""
    api_response = {
        "body": {
            "items": [{"itemName": "타이레놀정500mg"}],
            "totalCount": 1,
        }
    }

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=api_response)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.services.drug_info.cache_get_json", return_value=None), \
         patch("app.services.drug_info.cache_set_json") as mock_set, \
         patch("httpx.AsyncClient", return_value=mock_client):
        from app.services.drug_info import DrugInfoService
        service = DrugInfoService()
        result = await service.search_drug("타이레놀", 5)

    mock_set.assert_awaited_once()
    call_args = mock_set.call_args
    assert call_args.args[0] == "cache:drug:search:타이레놀:5"
    assert call_args.kwargs["ttl"] == 3600
    assert result.drugs[0].item_name == "타이레놀정500mg"
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_drug_search_cache_hit_skips_http app/tests/test_nfr_perf_003.py::test_drug_search_cache_miss_calls_http_and_stores -v 2>&1 | tail -15
```

Expected: 2 FAILED (ImportError or AttributeError — cache_get_json not in drug_info)

- [ ] **Step 3: `app/services/drug_info.py` 수정 — cache-aside 적용**

파일 전체를 다음으로 교체:

```python
import httpx

from app.core import config
from app.core.cache.client import TTL_DRUG_SEARCH, cache_get_json, cache_set_json
from app.dtos.drug_info import DrugInfo, DrugSearchResponse


def _drug_cache_key(drug_name: str, num_of_rows: int) -> str:
    return f"cache:drug:search:{drug_name}:{num_of_rows}"


class DrugInfoService:
    """식약처 의약품 정보 조회 (REQ-PILL-003)"""

    def __init__(self):
        self.api_key = config.DRUG_API_KEY
        self.base_url = config.DRUG_API_BASE_URL

    async def search_drug(self, drug_name: str, num_of_rows: int = 5) -> DrugSearchResponse:
        """약품명으로 의약품 정보 검색"""
        key = _drug_cache_key(drug_name, num_of_rows)
        cached = await cache_get_json(key)
        if cached is not None:
            return DrugSearchResponse.model_validate(cached)

        url = f"{self.base_url}/getDrbEasyDrugList"
        params = {
            "serviceKey": self.api_key,
            "itemName": drug_name,
            "type": "json",
            "numOfRows": num_of_rows,
            "pageNo": 1,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        body = data.get("body", {})
        items = body.get("items", [])
        total_count = body.get("totalCount", 0)

        if not isinstance(items, list):
            items = [items] if items else []

        drugs = []
        for item in items:
            drugs.append(
                DrugInfo(
                    item_name=item.get("itemName", ""),
                    entp_name=item.get("entpName"),
                    item_seq=item.get("itemSeq"),
                    efcy_qesitm=item.get("efcyQesitm"),
                    use_method_qesitm=item.get("useMethodQesitm"),
                    atpn_warn_qesitm=item.get("atpnWarnQesitm"),
                    atpn_qesitm=item.get("atpnQesitm"),
                    intrc_qesitm=item.get("intrcQesitm"),
                    se_qesitm=item.get("seQesitm"),
                    deposit_method_qesitm=item.get("depositMethodQesitm"),
                    item_image=item.get("itemImage"),
                )
            )

        result = DrugSearchResponse(
            query=drug_name,
            total_count=total_count,
            drugs=drugs,
        )
        await cache_set_json(key, result.model_dump(), ttl=TTL_DRUG_SEARCH)
        return result
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_drug_search_cache_hit_skips_http app/tests/test_nfr_perf_003.py::test_drug_search_cache_miss_calls_http_and_stores -v
```

Expected: 2 PASSED

- [ ] **Step 5: 커밋**

```bash
git add app/services/drug_info.py app/tests/test_nfr_perf_003.py
git commit -m "feat: NFR-PERF-003 DrugInfoService에 cache-aside 적용 (TTL 1시간)"
```

---

## Task 4: 사용자 프로필 캐시 (`GET /api/v1/users/me`)

**Files:**
- Create: `app/core/cache/user_cache_router.py`
- Modify: `app/main.py`
- Modify (append): `app/tests/test_nfr_perf_003.py`

전략: `user_routers.py` 수정 불가 → 새 라우터를 `v1_routers` 앞에 등록해 FastAPI 라우트 우선순위로 오버라이드.

캐시 키: `cache:user:profile:{user_id}`, TTL 600 s

- [ ] **Step 1: 사용자 프로필 캐시 테스트 추가**

`app/tests/test_nfr_perf_003.py` 끝에 추가:

```python
# ── 사용자 프로필 캐시 ────────────────────────────────────────

import json as _json

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient as HttpxAsyncClient


def _make_user_app() -> FastAPI:
    from app.core.cache.user_cache_router import user_cache_router
    app = FastAPI()
    app.include_router(user_cache_router, prefix="/api/v1")
    return app


def _make_token(user_id: int = 1) -> str:
    import jwt as _jwt
    from app.core import config as _cfg
    return _jwt.encode({"user_id": user_id, "token_type": "access"}, _cfg.SECRET_KEY, algorithm="HS256")


@pytest.mark.asyncio
async def test_user_me_cache_hit_skips_db() -> None:
    """캐시 히트 시 DB 조회를 하지 않는다."""
    cached_user = {
        "id": 1, "name": "테스터", "email": "test@example.com",
        "phone_number": "01011112222", "birthday": "1990-01-01",
        "gender": "MALE", "created_at": "2026-01-01T00:00:00",
    }
    token = _make_token(user_id=1)

    with patch("app.core.cache.user_cache_router.cache_get_json", return_value=cached_user), \
         patch("app.core.cache.user_cache_router.cache_set_json") as mock_set, \
         patch("app.core.cache.user_cache_router.UserRepository") as mock_repo_cls:
        app = _make_user_app()
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )

    mock_repo_cls.assert_not_called()
    mock_set.assert_not_called()
    assert resp.status_code == 200
    assert resp.json()["name"] == "테스터"


@pytest.mark.asyncio
async def test_user_me_cache_miss_queries_db_and_stores() -> None:
    """캐시 미스 시 DB를 조회하고 결과를 캐시에 저장한다."""
    from datetime import date, datetime
    from unittest.mock import MagicMock

    token = _make_token(user_id=2)

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

    with patch("app.core.cache.user_cache_router.cache_get_json", return_value=None), \
         patch("app.core.cache.user_cache_router.cache_set_json") as mock_set, \
         patch("app.core.cache.user_cache_router.UserRepository", return_value=mock_repo):
        app = _make_user_app()
        async with HttpxAsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )

    mock_set.assert_awaited_once()
    call_args = mock_set.call_args
    assert call_args.args[0] == "cache:user:profile:2"
    assert call_args.kwargs["ttl"] == 600
    assert resp.status_code == 200
    assert resp.json()["name"] == "신규유저"
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_user_me_cache_hit_skips_db app/tests/test_nfr_perf_003.py::test_user_me_cache_miss_queries_db_and_stores -v 2>&1 | tail -15
```

Expected: 2 FAILED (ImportError — user_cache_router not found)

- [ ] **Step 3: `app/core/cache/user_cache_router.py` 생성**

```python
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.cache.client import TTL_USER_PROFILE, cache_get_json, cache_set_json
from app.dtos.users import UserInfoResponse
from app.repositories.user_repository import UserRepository
from app.services.jwt import JwtService

user_cache_router = APIRouter(tags=["users"])

_security = HTTPBearer()


def _user_cache_key(user_id: int) -> str:
    return f"cache:user:profile:{user_id}"


async def _get_cached_user(
    credential: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
) -> UserInfoResponse:
    token = credential.credentials
    try:
        verified = JwtService().verify_jwt(token=token, token_type="access")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticate Failed.")

    user_id: int = verified.payload["user_id"]
    key = _user_cache_key(user_id)

    cached = await cache_get_json(key)
    if cached is not None:
        return UserInfoResponse.model_validate(cached)

    user = await UserRepository().get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticate Failed.")

    info = UserInfoResponse.model_validate(user)
    await cache_set_json(key, info.model_dump(mode="json"), ttl=TTL_USER_PROFILE)
    return info


@user_cache_router.get("/users/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def cached_user_me(
    info: Annotated[UserInfoResponse, Depends(_get_cached_user)],
) -> UserInfoResponse:
    """사용자 프로필 조회 (캐시 적용, TTL 10분)"""
    return info
```

- [ ] **Step 4: `app/main.py` 수정 — user_cache_router를 v1_routers 앞에 등록**

현재 `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import app.services.content_advertisement_filter  # noqa: F401 — NFR-COMPLI-003 pre_save signal 등록
import app.services.knowledge_source_validator  # noqa: F401 — NFR-SAFE-002 pre_save signal 등록
from app.apis.v1 import v1_routers
from app.core.db.databases import initialize_tortoise
from app.core.rate_limit.middleware import RateLimitMiddleware

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)
initialize_tortoise(app)
app.add_middleware(RateLimitMiddleware)

app.include_router(v1_routers)
```

다음으로 교체:

```python
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import app.services.content_advertisement_filter  # noqa: F401 — NFR-COMPLI-003 pre_save signal 등록
import app.services.knowledge_source_validator  # noqa: F401 — NFR-SAFE-002 pre_save signal 등록
from app.apis.v1 import v1_routers
from app.apis.v1.health_guide_routers import health_guide_router
from app.core.cache.user_cache_router import user_cache_router
from app.core.db.databases import initialize_tortoise
from app.core.rate_limit.middleware import RateLimitMiddleware

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)
initialize_tortoise(app)
app.add_middleware(RateLimitMiddleware)

# 캐시 라우터를 먼저 등록해 /users/me 우선순위 확보 (NFR-PERF-003)
app.include_router(user_cache_router, prefix="/api/v1")
app.include_router(health_guide_router, prefix="/api/v1")  # NFR-PERF-003: GET /{id} 포함
app.include_router(v1_routers)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_user_me_cache_hit_skips_db app/tests/test_nfr_perf_003.py::test_user_me_cache_miss_queries_db_and_stores -v
```

Expected: 2 PASSED

- [ ] **Step 6: 커밋**

```bash
git add app/core/cache/user_cache_router.py app/main.py app/tests/test_nfr_perf_003.py
git commit -m "feat: NFR-PERF-003 사용자 프로필 캐시 라우터 (TTL 10분) + main.py 등록"
```

---

## Task 5: 가이드 상세 캐시 (`GET /api/v1/health-guides/{guide_id}`)

**Files:**
- Modify: `app/services/health_guides.py`
- Modify: `app/apis/v1/health_guide_routers.py`
- Modify (append): `app/tests/test_nfr_perf_003.py`

캐시 키: `cache:guide:detail:{guide_id}`, TTL 1800 s
캐시 무효화: `generate_guide()` 내 `update_result()` 호출 후

- [ ] **Step 1: 가이드 상세 캐시 테스트 추가**

`app/tests/test_nfr_perf_003.py` 끝에 추가:

```python
# ── 가이드 상세 캐시 ──────────────────────────────────────────

from uuid import UUID as _UUID


@pytest.mark.asyncio
async def test_guide_cache_hit_skips_repo() -> None:
    """캐시 히트 시 레포지토리 조회를 건너뛴다."""
    guide_id = "11111111-1111-1111-1111-111111111111"
    cached_guide = {
        "id": guide_id,
        "guide_type": "GENERAL",
        "status": "COMPLETED",
        "user_question": "두통이 심해요",
        "guide_content": "충분한 수분 섭취를 권장합니다.",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }

    with patch("app.services.health_guides.cache_get_json", return_value=cached_guide), \
         patch("app.services.health_guides.cache_set_json") as mock_set, \
         patch("app.services.health_guides.HealthGuideRepository") as mock_repo_cls:
        from app.services.health_guides import HealthGuideService
        service = HealthGuideService.__new__(HealthGuideService)
        service.repo = MagicMock()
        result = await service.get_guide_by_id(_UUID(guide_id))

    mock_repo_cls.assert_not_called()
    mock_set.assert_not_called()
    assert result is not None
    assert result.guide_content == "충분한 수분 섭취를 권장합니다."


@pytest.mark.asyncio
async def test_guide_cache_miss_queries_repo_and_stores() -> None:
    """캐시 미스 시 레포지토리를 조회하고 결과를 캐시에 저장한다."""
    from datetime import datetime
    from uuid import uuid4

    guide_id = uuid4()
    mock_guide = MagicMock()
    mock_guide.id = guide_id
    mock_guide.guide_type = "GENERAL"
    mock_guide.status = "COMPLETED"
    mock_guide.user_question = "두통이 심해요"
    mock_guide.guide_content = "충분한 수분 섭취를 권장합니다."
    mock_guide.created_at = datetime(2026, 1, 1)
    mock_guide.updated_at = datetime(2026, 1, 1)

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_guide)

    with patch("app.services.health_guides.cache_get_json", return_value=None), \
         patch("app.services.health_guides.cache_set_json") as mock_set:
        from app.services.health_guides import HealthGuideService
        service = HealthGuideService.__new__(HealthGuideService)
        service.repo = mock_repo
        result = await service.get_guide_by_id(guide_id)

    mock_set.assert_awaited_once()
    call_args = mock_set.call_args
    assert call_args.args[0] == f"cache:guide:detail:{guide_id}"
    assert call_args.kwargs["ttl"] == 1800
    assert result is not None


@pytest.mark.asyncio
async def test_guide_cache_invalidated_on_update() -> None:
    """update_result 호출 시 해당 가이드 캐시가 삭제된다."""
    from uuid import uuid4

    guide_id = uuid4()
    mock_guide = MagicMock()
    mock_guide.id = guide_id
    mock_guide.guide_content = None
    mock_guide.status = "PENDING"
    mock_guide.save = AsyncMock()

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_guide)

    with patch("app.services.health_guides.cache_delete") as mock_del, \
         patch.object(mock_guide, "save", new=AsyncMock()):
        from app.services.health_guides import HealthGuideService
        service = HealthGuideService.__new__(HealthGuideService)
        service.repo = mock_repo
        await service._update_and_invalidate(guide_id, "가이드 내용", "COMPLETED")

    mock_del.assert_awaited_once_with(f"cache:guide:detail:{guide_id}")
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_guide_cache_hit_skips_repo app/tests/test_nfr_perf_003.py::test_guide_cache_miss_queries_repo_and_stores app/tests/test_nfr_perf_003.py::test_guide_cache_invalidated_on_update -v 2>&1 | tail -20
```

Expected: 3 FAILED

- [ ] **Step 3: `app/services/health_guides.py` 수정**

파일 전체를 다음으로 교체:

```python
from datetime import datetime
from uuid import UUID

from openai import OpenAI

from app.core import config
from app.core.cache.client import TTL_GUIDE_DETAIL, cache_delete, cache_get_json, cache_set_json
from app.dtos.health_guides import (
    HealthGuideCreateRequest,
    HealthGuideListResponse,
    HealthGuideResponse,
)
from app.models.health_guides import GuideStatus
from app.models.notifications import NotificationType
from app.models.prompts import PromptType
from app.repositories.health_guide_repository import HealthGuideRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.prompt_repository import PromptRepository


def _guide_cache_key(guide_id: UUID) -> str:
    return f"cache:guide:detail:{guide_id}"


class HealthGuideService:
    def __init__(self):
        self.repo = HealthGuideRepository()
        self.prompt_repo = PromptRepository()
        self.noti_repo = NotificationRepository()
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    async def get_my_guides(self, user_id: UUID) -> HealthGuideListResponse:
        guides = await self.repo.get_user_guides(user_id)
        return HealthGuideListResponse(
            guides=[HealthGuideResponse.model_validate(g) for g in guides],
            total=len(guides),
        )

    async def get_guide_by_id(self, guide_id: UUID) -> HealthGuideResponse | None:
        """가이드 상세 조회 (캐시 적용, TTL 30분)"""
        key = _guide_cache_key(guide_id)
        cached = await cache_get_json(key)
        if cached is not None:
            return HealthGuideResponse.model_validate(cached)

        guide = await self.repo.get_by_id(guide_id)
        if guide is None:
            return None

        result = HealthGuideResponse.model_validate(guide)
        await cache_set_json(key, result.model_dump(mode="json"), ttl=TTL_GUIDE_DETAIL)
        return result

    async def _update_and_invalidate(self, guide_id: UUID, content: str, status: str) -> None:
        """가이드 내용 저장 후 캐시 무효화."""
        guide = await self.repo.get_by_id(guide_id)
        if guide:
            guide.guide_content = content
            guide.status = status
            await guide.save()
        await cache_delete(_guide_cache_key(guide_id))

    async def generate_guide(self, user_id: UUID, data: HealthGuideCreateRequest) -> HealthGuideResponse:
        """AI 가이드 생성!"""
        guide = await self.repo.create(
            user_id=user_id,
            guide_type=data.guide_type,
            user_question=data.user_question,
        )

        try:
            guide.status = GuideStatus.PROCESSING
            await guide.save()

            active_prompt = await self.prompt_repo.get_active(PromptType.HEALTH_GUIDE)

            if active_prompt:
                system_prompt = active_prompt.template_text
            else:
                system_prompt = "당신은 건강 가이드 전문가입니다. 사용자의 질문에 친절하고 정확하게 답변해주세요."

            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": data.user_question},
                ],
                max_tokens=1500,
            )

            guide_content = response.choices[0].message.content
            await self.repo.update_result(
                guide_id=guide.id,
                guide_content=guide_content,
                status=GuideStatus.COMPLETED,
            )
            await cache_delete(_guide_cache_key(guide.id))
            guide = await self.repo.get_by_id(guide.id)

            await self.noti_repo.create_notification(
                user_id=user_id,
                notification_type=NotificationType.GUIDE,
                title="새로운 맞춤 가이드가 도착했습니다",
                content="새로운 맞춤 가이드가 도착했습니다. 지금 확인해보세요!",
                scheduled_at=datetime.now(),
            )

        except Exception as e:
            await self.repo.update_result(
                guide_id=guide.id,
                guide_content=f"가이드 생성 실패: {str(e)}",
                status=GuideStatus.FAILED,
            )
            await cache_delete(_guide_cache_key(guide.id))
            guide = await self.repo.get_by_id(guide.id)

        return HealthGuideResponse.model_validate(guide)
```

- [ ] **Step 4: `app/apis/v1/health_guide_routers.py` — GET /{guide_id} 추가**

파일 끝에 다음 엔드포인트를 추가:

```python
from uuid import UUID

# ... (기존 import에 추가 없이 — UUID는 이미 Python 표준)
```

기존 파일 맨 끝에 추가:

```python
@health_guide_router.get(
    "/{guide_id}",
    response_model=HealthGuideResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_guide_detail(
    guide_id: UUID,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthGuideService, Depends(HealthGuideService)],
) -> Response:
    """가이드 상세 조회 (캐시 적용, REQ-GUIDE-001)"""
    result = await service.get_guide_by_id(guide_id)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
```

`health_guide_routers.py` 상단 import에 `UUID` 추가:

```python
from uuid import UUID
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py::test_guide_cache_hit_skips_repo app/tests/test_nfr_perf_003.py::test_guide_cache_miss_queries_repo_and_stores app/tests/test_nfr_perf_003.py::test_guide_cache_invalidated_on_update -v
```

Expected: 3 PASSED

- [ ] **Step 6: 커밋**

```bash
git add app/services/health_guides.py app/apis/v1/health_guide_routers.py app/tests/test_nfr_perf_003.py
git commit -m "feat: NFR-PERF-003 가이드 상세 캐시 (TTL 30분, 수정 시 무효화) + GET /{guide_id} 엔드포인트"
```

---

## Task 6: ruff + 전체 테스트 통과

**Files:**
- (없음 — 검증만)

- [ ] **Step 1: ruff 린트 + 포맷 검사**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run ruff check app/core/cache/ app/services/drug_info.py app/services/health_guides.py app/apis/v1/health_guide_routers.py app/main.py app/tests/test_nfr_perf_003.py
```

Expected: 오류 없음

- [ ] **Step 2: ruff 포맷 검사**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run ruff format --check app/core/cache/ app/services/drug_info.py app/services/health_guides.py app/apis/v1/health_guide_routers.py app/main.py app/tests/test_nfr_perf_003.py
```

Expected: 오류 없음. 포맷 오류가 있으면:

```bash
cd ~/PycharmProjects/AH_03_07 && uv run ruff format app/core/cache/ app/services/drug_info.py app/services/health_guides.py app/apis/v1/health_guide_routers.py app/main.py app/tests/test_nfr_perf_003.py
```

- [ ] **Step 3: NFR-PERF-003 전체 테스트 실행**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/test_nfr_perf_003.py -v
```

Expected: 8 PASSED

- [ ] **Step 4: 기존 테스트 회귀 확인**

```bash
cd ~/PycharmProjects/AH_03_07 && uv run pytest app/tests/ -v --ignore=app/tests/test_nfr_perf_003.py -x 2>&1 | tail -20
```

Expected: 기존 테스트 모두 PASSED (Redis/DB 연결 오류는 건너뜀)

- [ ] **Step 5: ruff 수정 사항 있으면 커밋**

```bash
git add -u
git commit -m "style: NFR-PERF-003 ruff format 정리"
```

---

## Task 7: push

- [ ] **Step 1: 전체 커밋 확인**

```bash
git log --oneline origin/develop..HEAD
```

Expected (최소 4개 커밋):
```
style: NFR-PERF-003 ruff format 정리        (있을 경우)
feat: NFR-PERF-003 가이드 상세 캐시 ...
feat: NFR-PERF-003 사용자 프로필 캐시 ...
feat: NFR-PERF-003 DrugInfoService에 cache-aside ...
feat: NFR-PERF-003 cache client — get/set/delete ...
```

- [ ] **Step 2: push**

```bash
git push -u origin feature/nfr-perf-003
```

---

## Self-Review

### Spec 커버리지 체크

| 요구사항 | Task | 상태 |
|---------|------|------|
| Cache-Aside 패턴 | Task 3–5 | ✓ |
| 약품 마스터 GET /drug-info/search, TTL 1시간 | Task 3 | ✓ |
| 사용자 프로필 GET /users/me, TTL 10분 | Task 4 | ✓ |
| 가이드 상세 GET /health-guides/{id}, TTL 30분 | Task 5 | ✓ |
| 가이드 수정 시 무효화 | Task 5 `_update_and_invalidate` | ✓ |
| 캐시 저장소: Redis | Task 2 | ✓ |

### Placeholder 스캔
- 모든 Step에 실제 코드 포함 ✓
- "TBD", "TODO" 없음 ✓

### 타입 일관성
- `cache_get_json` / `cache_set_json` / `cache_delete` Task 2에서 정의 → Task 3–5에서 동일 이름 사용 ✓
- `TTL_DRUG_SEARCH = 3600`, `TTL_USER_PROFILE = 600`, `TTL_GUIDE_DETAIL = 1800` Task 2에서 정의 → Task 3–5에서 임포트 ✓
- `_guide_cache_key`, `_drug_cache_key`, `_user_cache_key` 각 Task에서 독립 정의 (DRY — 각 모듈 내에서만 사용) ✓