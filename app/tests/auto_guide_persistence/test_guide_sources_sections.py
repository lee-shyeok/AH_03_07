from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from tortoise.contrib.test import TestCase

from app.guide_generator.schema import SourceItem
from app.main import app
from app.models.auto_guide import AutoGuide, AutoGuideStatus
from app.models.users import User

BASE_URL = "http://test"

_SOURCES = [
    SourceItem(
        title="류마티스관절염 진료지침",
        section="약물 치료",
        page=42,
        organization="대한류마티스학회",
        published_year=2023,
        score=0.91,
    ),
    SourceItem(
        title="루푸스 임상 가이드",
        section="검사 모니터링",
        page=18,
        organization="대한내과학회",
        published_year=2022,
        score=0.85,
    ),
]

_SIDE_EFFECTS = ["두통", "구역", "복통"]


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "가이드테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": phone,
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return resp.json()["access_token"]


async def _create_guide(user_id: int) -> int:
    guide = await AutoGuide.create(
        user_id=user_id,
        status=AutoGuideStatus.GENERATED,
        medication_general="약물 복용 시 의료진 지시를 따르세요.",
        side_effect_monitoring=_SIDE_EFFECTS,
        lifestyle_info="규칙적인 생활을 유지하세요.",
        symptom_summary="증상 변화를 다음 진료 시 공유하세요.",
        sources=[s.model_dump() for s in _SOURCES],
        disclaimer="※ 이 안내문은 의료 진단·처방·치료를 대체하지 않습니다.",
    )
    return guide.id


class TestGuideSources(TestCase):
    async def test_sources_200_mapping(self):
        """본인 가이드 sources 조회 → 200, 길이·필드 매핑 정확."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "src_owner@example.com", "01096000001")
            user = await User.get(email="src_owner@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sources",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == len(_SOURCES)

    async def test_sources_citation_order_is_1_based(self):
        """citation_order가 1부터 순서대로 부여된다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "src_order@example.com", "01096000002")
            user = await User.get(email="src_order@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sources",
                headers={"Authorization": f"Bearer {token}"},
            )

        items = resp.json()
        orders = [item["citation_order"] for item in items]
        assert orders == list(range(1, len(_SOURCES) + 1))

    async def test_sources_field_mapping(self):
        """source_title/source_org/source_page/used_for_section이 SourceItem에서 올바르게 매핑된다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "src_fields@example.com", "01096000003")
            user = await User.get(email="src_fields@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sources",
                headers={"Authorization": f"Bearer {token}"},
            )

        items = resp.json()
        first = items[0]
        assert first["source_title"] == _SOURCES[0].title
        assert first["source_org"] == _SOURCES[0].organization
        assert first["source_page"] == _SOURCES[0].page
        assert first["used_for_section"] == _SOURCES[0].section

    async def test_sources_other_user_404(self):
        """다른 유저의 guide_id로 조회하면 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "src_usera@example.com", "01096000004")
            user_a = await User.get(email="src_usera@example.com")
            guide_id = await _create_guide(user_a.id)

            token_b = await _signup_and_login(client, "src_userb@example.com", "01096000005")
            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sources",
                headers={"Authorization": f"Bearer {token_b}"},
            )

        assert resp.status_code == 404

    async def test_sources_nonexistent_404(self):
        """존재하지 않는 guide_id → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "src_miss@example.com", "01096000006")

            resp = await client.get(
                "/api/v1/guides/999999999/sources",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404


class TestGuideSections(TestCase):
    async def test_sections_200_four_items(self):
        """본인 가이드 sections 조회 → 200, 항목 4개."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sec_owner@example.com", "01096000007")
            user = await User.get(email="sec_owner@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sections",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        assert len(resp.json()) == 4

    async def test_sections_display_order_1_to_4(self):
        """display_order가 1~4 순서로 반환된다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sec_order@example.com", "01096000008")
            user = await User.get(email="sec_order@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sections",
                headers={"Authorization": f"Bearer {token}"},
            )

        orders = [s["display_order"] for s in resp.json()]
        assert orders == [1, 2, 3, 4]

    async def test_sections_section_types(self):
        """section_type 값이 명세 순서대로 반환된다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sec_types@example.com", "01096000009")
            user = await User.get(email="sec_types@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sections",
                headers={"Authorization": f"Bearer {token}"},
            )

        types = [s["section_type"] for s in resp.json()]
        assert types == ["MEDICATION_GENERAL", "SIDE_EFFECT", "LIFESTYLE", "SYMPTOM_SUMMARY"]

    async def test_sections_side_effect_joined_with_newline(self):
        """side_effect_monitoring(list) → section_content가 \\n으로 join된다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sec_join@example.com", "01096000010")
            user = await User.get(email="sec_join@example.com")
            guide_id = await _create_guide(user.id)

            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sections",
                headers={"Authorization": f"Bearer {token}"},
            )

        sections = resp.json()
        side_effect = next(s for s in sections if s["section_type"] == "SIDE_EFFECT")
        assert side_effect["section_content"] == "\n".join(_SIDE_EFFECTS)

    async def test_sections_other_user_404(self):
        """다른 유저의 guide_id로 sections 조회하면 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "sec_usera@example.com", "01096000011")
            user_a = await User.get(email="sec_usera@example.com")
            guide_id = await _create_guide(user_a.id)

            token_b = await _signup_and_login(client, "sec_userb@example.com", "01096000012")
            resp = await client.get(
                f"/api/v1/guides/{guide_id}/sections",
                headers={"Authorization": f"Bearer {token_b}"},
            )

        assert resp.status_code == 404

    async def test_sections_nonexistent_404(self):
        """존재하지 않는 guide_id → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sec_miss@example.com", "01096000013")

            resp = await client.get(
                "/api/v1/guides/999999999/sections",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404
