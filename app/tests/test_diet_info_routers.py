"""REQ-DIET-001 — 식이 정보 외부 링크 라우터 테스트."""

from unittest.mock import MagicMock
from urllib.parse import quote

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.security import get_request_user
from app.main import app
from app.models.users import User

_EXPECTED_SOURCES = {
    "식약처 의약품안전나라",
    "약학정보원",
    "대한류마티스학회",
    "KDCA 만성질환 정보",
}


def _mock_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = 1
    return user


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_request_user] = _mock_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_known_drug_returns_200_with_4_links() -> None:
    """정상 약품명 → 200 + 4개 외부 링크."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/diet-info", params={"drug_name": "타크로리무스"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["drug_name"] == "타크로리무스"
    assert len(body["external_links"]) == 4
    sources = {link["source"] for link in body["external_links"]}
    assert sources == _EXPECTED_SOURCES
    assert body["disclaimer"]


@pytest.mark.asyncio
async def test_empty_drug_name_returns_422() -> None:
    """빈 drug_name → 422 Unprocessable Entity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/diet-info", params={"drug_name": ""})

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_unauthenticated_returns_401() -> None:
    """비인증 요청 → 401."""
    app.dependency_overrides.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/diet-info", params={"drug_name": "메토트렉세이트"})

    assert resp.status_code == 401
    app.dependency_overrides[get_request_user] = _mock_user


@pytest.mark.asyncio
async def test_korean_drug_name_url_encoded_correctly() -> None:
    """한글 약품명 → URL에 퍼센트 인코딩 적용."""
    drug = "하이드록시클로로퀸"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/diet-info", params={"drug_name": drug})

    assert resp.status_code == 200
    links = {link["source"]: link["url"] for link in resp.json()["external_links"]}
    encoded = quote(drug)
    assert encoded in links["식약처 의약품안전나라"]
    assert encoded in links["약학정보원"]
