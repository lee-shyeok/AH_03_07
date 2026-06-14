"""안내문 소프트 삭제 API 테스트 (REQ-AUTO-005)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.auto_guide import AutoGuide, AutoGuideStatus
from app.models.users import User

BASE_URL = "http://test"


async def _signup_and_get_token(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "삭제테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": phone,
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return res.json().get("access_token", "")


async def _create_guide(user_id: int) -> AutoGuide:
    return await AutoGuide.create(
        user_id=user_id,
        status=AutoGuideStatus.GENERATED,
        medication_general="약물 안내",
        side_effect_monitoring=["두통"],
        lifestyle_info="규칙적 생활",
        symptom_summary="증상 요약",
        sources=[],
        disclaimer="※ 진단 대체 불가.",
    )


class TestGuideDelete(TestCase):
    async def test_delete_guide_returns_204(self):
        """소유한 안내문 삭제 → 204."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_get_token(client, "del_204@example.com", "01097100001")
            user = await User.get(email="del_204@example.com")
            guide = await _create_guide(user.id)

            res = await client.delete(
                f"/api/v1/guides/{guide.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 204

    async def test_deleted_guide_not_in_list(self):
        """삭제 후 목록 조회 → 해당 안내문 없음."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_get_token(client, "del_list@example.com", "01097100002")
            user = await User.get(email="del_list@example.com")
            guide = await _create_guide(user.id)

            await client.delete(
                f"/api/v1/guides/{guide.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            list_res = await client.get(
                "/api/v1/guides",
                headers={"Authorization": f"Bearer {token}"},
            )

        items = list_res.json().get("items", [])
        ids = [g["id"] for g in items]
        assert guide.id not in ids

    async def test_deleted_guide_detail_returns_404(self):
        """삭제 후 상세 조회 → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_get_token(client, "del_404@example.com", "01097100003")
            user = await User.get(email="del_404@example.com")
            guide = await _create_guide(user.id)

            await client.delete(
                f"/api/v1/guides/{guide.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            detail_res = await client.get(
                f"/api/v1/guides/{guide.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert detail_res.status_code == 404

    async def test_delete_nonexistent_guide_returns_404(self):
        """존재하지 않는 안내문 삭제 → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_get_token(client, "del_noexist@example.com", "01097100004")

            res = await client.delete(
                "/api/v1/guides/99999999",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 404

    async def test_delete_other_users_guide_returns_404(self):
        """타 사용자 안내문 삭제 시도 → 404 (소유 검증)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            # 소유자 A
            await _signup_and_get_token(client, "del_owner@example.com", "01097100005")
            owner = await User.get(email="del_owner@example.com")
            guide = await _create_guide(owner.id)

            # 다른 사용자 B
            token_b = await _signup_and_get_token(client, "del_other@example.com", "01097100006")
            res = await client.delete(
                f"/api/v1/guides/{guide.id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert res.status_code == 404

    async def test_deleted_at_set_in_db(self):
        """삭제 후 DB의 deleted_at 필드가 채워진다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_get_token(client, "del_dtat@example.com", "01097100007")
            user = await User.get(email="del_dtat@example.com")
            guide = await _create_guide(user.id)

            await client.delete(
                f"/api/v1/guides/{guide.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        refreshed = await AutoGuide.get(id=guide.id)
        assert refreshed.deleted_at is not None
