"""NFR-SAFE-003 — 관리자 안전 필터 로그 API 테스트."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.safety_filter_log import SafetyFilterLog

BASE_URL = "http://test"
LOGS_EP = "/api/v1/admin/safety-filter-logs"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": phone,
        },
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


async def _make_admin(email: str) -> None:
    from app.models.users import User

    await User.filter(email=email).update(is_admin=True)


class TestAdminSafetyFilterLogsApi(TestCase):
    async def test_unauthenticated_returns_401(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(LOGS_EP)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_non_admin_returns_403(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_nonadmin@example.com", "01093000001")
            resp = await client.get(LOGS_EP, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    async def test_admin_empty_logs_returns_empty_list(self) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_admin_empty@example.com", "01093000002")
            await _make_admin("sfl_admin_empty@example.com")
            resp = await client.get(LOGS_EP, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    async def test_admin_sees_all_logs(self) -> None:
        await SafetyFilterLog.create(
            user_id=999,
            target_type="CHAT",
            target_id="msg-001",
            blocked_reason="diagnosis_presumption",
            original_text="루푸스로 보입니다.",
            safe_replacement_text="이 부분은 담당 의료진 또는 약사 상담이 필요합니다",
            filter_stage="post_generation",
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_admin_list@example.com", "01093000003")
            await _make_admin("sfl_admin_list@example.com")
            resp = await client.get(LOGS_EP, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] >= 1
        item = body["items"][0]
        assert "id" in item
        assert "user_id" in item
        assert "blocked_reason" in item
        assert "message_preview" in item
        assert "filter_stage" in item
        assert "created_at" in item

    async def test_message_preview_truncated_to_100_chars(self) -> None:
        long_text = "가" * 200
        await SafetyFilterLog.create(
            user_id=888,
            target_type="GUIDE",
            target_id=None,
            blocked_reason="drug_modification",
            original_text=long_text,
            safe_replacement_text="이 부분은 담당 의료진 또는 약사 상담이 필요합니다",
            filter_stage="post_generation",
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_preview@example.com", "01093000004")
            await _make_admin("sfl_preview@example.com")
            resp = await client.get(
                LOGS_EP,
                params={"user_id": 888},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        items = resp.json()["items"]
        assert len(items) >= 1
        assert len(items[0]["message_preview"]) <= 100

    async def test_filter_by_user_id(self) -> None:
        await SafetyFilterLog.create(
            user_id=777,
            target_type="CHAT",
            target_id="msg-777",
            blocked_reason="diagnosis_presumption",
            original_text="루푸스로 보입니다.",
            safe_replacement_text="이 부분은 담당 의료진 또는 약사 상담이 필요합니다",
            filter_stage="post_generation",
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_filter_uid@example.com", "01093000005")
            await _make_admin("sfl_filter_uid@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            resp_match = await client.get(LOGS_EP, params={"user_id": 777}, headers=headers)
            resp_no_match = await client.get(LOGS_EP, params={"user_id": 99999}, headers=headers)
        assert resp_match.status_code == status.HTTP_200_OK
        assert any(i["user_id"] == 777 for i in resp_match.json()["items"])
        assert resp_no_match.json()["total"] == 0

    async def test_filter_by_blocked_reason(self) -> None:
        await SafetyFilterLog.create(
            user_id=666,
            target_type="CHAT",
            target_id=None,
            blocked_reason="treatment_recommendation",
            original_text="이부프로펜을 복용하세요.",
            safe_replacement_text="이 부분은 담당 의료진 또는 약사 상담이 필요합니다",
            filter_stage="post_generation",
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_filter_reason@example.com", "01093000006")
            await _make_admin("sfl_filter_reason@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(LOGS_EP, params={"blocked_reason": "treatment"}, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        items = resp.json()["items"]
        assert all("treatment" in i["blocked_reason"] for i in items)

    async def test_pagination_limit_offset(self) -> None:
        for i in range(5):
            await SafetyFilterLog.create(
                user_id=555,
                target_type="CHAT",
                target_id=f"msg-page-{i}",
                blocked_reason="lab_interpretation",
                original_text="수치가 위험합니다.",
                safe_replacement_text="이 부분은 담당 의료진 또는 약사 상담이 필요합니다",
                filter_stage="post_generation",
            )
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sfl_page@example.com", "01093000007")
            await _make_admin("sfl_page@example.com")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                LOGS_EP,
                params={"user_id": 555, "limit": 2, "offset": 0},
                headers=headers,
            )
        body = resp.json()
        assert resp.status_code == status.HTTP_200_OK
        assert body["total"] == 5
        assert len(body["items"]) == 2
