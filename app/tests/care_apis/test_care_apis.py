from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "보호자테스터",
        "gender": "MALE",
        "birth_date": "1990-01-01",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestGuardianApis(TestCase):
    """POST/GET /api/v1/guardians"""

    async def test_create_guardian_returns_201(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "grd_create@example.com", "01011110001")
            resp = await client.post(
                "/api/v1/guardians",
                json={"name": "홍길동", "phone_number": "01099990001", "relationship": "부모"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["name"] == "홍길동"
        assert body["relationship"] == "부모"
        assert body["is_active"] is True

    async def test_list_guardians_returns_created_entry(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "grd_list@example.com", "01011110002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/guardians",
                json={"name": "이순신", "relationship": "배우자"},
                headers=headers,
            )
            resp = await client.get("/api/v1/guardians", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 1
        assert body["guardians"][0]["name"] == "이순신"

    async def test_create_guardian_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post("/api/v1/guardians", json={"name": "무인증"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestShareLinkApis(TestCase):
    """POST/GET/DELETE /api/v1/guardians/shares"""

    async def _create_guardian(self, client: AsyncClient, headers: dict) -> str:
        resp = await client.post(
            "/api/v1/guardians",
            json={"name": "공유테스트보호자", "relationship": "형제"},
            headers=headers,
        )
        return resp.json()["id"]

    async def test_create_share_link_returns_201(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "share_create@example.com", "01022220001")
            headers = {"Authorization": f"Bearer {token}"}
            guardian_id = await self._create_guardian(client, headers)
            resp = await client.post(
                "/api/v1/guardians/shares",
                json={
                    "guardian_id": guardian_id,
                    "duration": "ONE_WEEK",
                    "categories": ["medication", "schedule"],
                    "include_summary_only": True,
                },
                headers=headers,
            )
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["guardian_id"] == guardian_id
        assert body["is_revoked"] is False
        assert "token" in body

    async def test_list_share_links_returns_created_entry(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "share_list@example.com", "01022220002")
            headers = {"Authorization": f"Bearer {token}"}
            guardian_id = await self._create_guardian(client, headers)
            await client.post(
                "/api/v1/guardians/shares",
                json={
                    "guardian_id": guardian_id,
                    "duration": "ONE_DAY",
                    "categories": ["lab_result"],
                    "include_summary_only": False,
                },
                headers=headers,
            )
            resp = await client.get("/api/v1/guardians/shares", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 1
        assert body["share_links"][0]["categories"] == ["lab_result"]

    async def test_revoke_share_link_returns_revoked(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "share_revoke@example.com", "01022220003")
            headers = {"Authorization": f"Bearer {token}"}
            guardian_id = await self._create_guardian(client, headers)
            create_resp = await client.post(
                "/api/v1/guardians/shares",
                json={
                    "guardian_id": guardian_id,
                    "duration": "ONE_MONTH",
                    "categories": ["diagnosis"],
                    "include_summary_only": True,
                },
                headers=headers,
            )
            link_id = create_resp.json()["id"]
            revoke_resp = await client.delete(f"/api/v1/guardians/shares/{link_id}", headers=headers)
        assert revoke_resp.status_code == status.HTTP_200_OK
        assert revoke_resp.json()["is_revoked"] is True

    async def test_share_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/guardians/shares")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestGuardianViewApi(TestCase):
    """GET /api/v1/guardians/view/{token}"""

    async def _setup_share(self, client: AsyncClient, email: str, phone: str) -> str:
        token = await _signup_and_login(client, email, phone)
        headers = {"Authorization": f"Bearer {token}"}
        guardian_resp = await client.post(
            "/api/v1/guardians",
            json={"name": "열람테스트보호자", "relationship": "자녀"},
            headers=headers,
        )
        guardian_id = guardian_resp.json()["id"]
        share_resp = await client.post(
            "/api/v1/guardians/shares",
            json={
                "guardian_id": guardian_id,
                "duration": "ONE_WEEK",
                "categories": ["medication", "lab_result"],
                "include_summary_only": True,
            },
            headers=headers,
        )
        return share_resp.json()["token"]

    async def test_view_with_valid_token_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            share_token = await self._setup_share(client, "view_valid@example.com", "01033330001")
            resp = await client.get(f"/api/v1/guardians/view/{share_token}")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "medication" in body["categories"]
        assert "share_id" in body
        assert body["include_summary_only"] is True

    async def test_view_with_invalid_token_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/guardians/view/invalid-token-xyz")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_view_with_revoked_token_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            share_token = await self._setup_share(client, "view_revoke@example.com", "01033330002")
            # 공유 링크 목록 조회 → id 확인 → 철회
            login_resp = await client.post(
                "/api/v1/auth/login", json={"email": "view_revoke@example.com", "password": "Password123!"}
            )
            headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
            shares = await client.get("/api/v1/guardians/shares", headers=headers)
            link_id = shares.json()["share_links"][0]["id"]
            await client.delete(f"/api/v1/guardians/shares/{link_id}", headers=headers)
            # 철회 후 token으로 열람 시도
            resp = await client.get(f"/api/v1/guardians/view/{share_token}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_view_does_not_require_auth(self):
        """token만으로 인증 없이 접근 가능해야 함"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            share_token = await self._setup_share(client, "view_noauth@example.com", "01033330003")
            # Authorization 헤더 없이 접근
            resp = await client.get(f"/api/v1/guardians/view/{share_token}")
        assert resp.status_code == status.HTTP_200_OK
