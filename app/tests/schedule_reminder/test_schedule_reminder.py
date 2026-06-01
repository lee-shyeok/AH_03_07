from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.notifications import Notification, NotificationType
from app.models.users import User

BASE_URL = "http://test"
SCHEDULES_EP = "/api/v1/care-schedules"
KST = ZoneInfo("Asia/Seoul")

FORBIDDEN_WORDS = ["드세요", "복용", "검사를 받으세요", "결과가", "권장"]

_BASE_PAYLOAD = {
    "schedule_type": "BLOOD_TEST",
    "title": "정기 혈액검사",
    "scheduled_date": "2026-08-01",
    "reminder_days_before": 1,
}


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "리마인더테스터",
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


class TestScheduleReminder(TestCase):
    async def test_create_schedule_generates_one_schedule_notification(self):
        """일정 생성 → SCHEDULE 타입 알림 1개 생성됨"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "reminder_basic@example.com", "01093000001")
            await client.post(
                SCHEDULES_EP,
                json=_BASE_PAYLOAD,
                headers={"Authorization": f"Bearer {token}"},
            )
        user = await User.get(email="reminder_basic@example.com")
        notifs = await Notification.filter(user_id=user.id, notification_type=NotificationType.SCHEDULE).all()
        assert len(notifs) == 1

    async def test_scheduled_at_uses_reminder_days_before(self):
        """reminder_days_before=1 → scheduled_at = (scheduled_date − 1일) 09:00 KST"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "reminder_time@example.com", "01093000002")
            await client.post(
                SCHEDULES_EP,
                json={**_BASE_PAYLOAD, "schedule_type": "APPOINTMENT", "title": "외래 진료", "reminder_days_before": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
        user = await User.get(email="reminder_time@example.com")
        notif = await Notification.filter(user_id=user.id, notification_type=NotificationType.SCHEDULE).first()
        scheduled_at_kst = notif.scheduled_at.astimezone(KST)
        assert scheduled_at_kst.date() == date(2026, 7, 31)  # 2026-08-01 − 1일
        assert scheduled_at_kst.hour == 9
        assert scheduled_at_kst.minute == 0

    async def test_reminder_days_before_3_shifts_notification_date(self):
        """reminder_days_before=3 → scheduled_at = (scheduled_date − 3일) 09:00 KST"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "reminder_3days@example.com", "01093000008")
            await client.post(
                SCHEDULES_EP,
                json={**_BASE_PAYLOAD, "reminder_days_before": 3, "scheduled_date": "2026-09-10"},
                headers={"Authorization": f"Bearer {token}"},
            )
        user = await User.get(email="reminder_3days@example.com")
        notif = await Notification.filter(user_id=user.id, notification_type=NotificationType.SCHEDULE).first()
        scheduled_at_kst = notif.scheduled_at.astimezone(KST)
        assert scheduled_at_kst.date() == date(2026, 9, 7)  # 2026-09-10 − 3일
        assert scheduled_at_kst.hour == 9

    async def test_each_schedule_type_produces_correct_label_title_content(self):
        """각 schedule_type → 올바른 라벨·title·content"""
        type_to_label = [
            ("BLOOD_TEST", "정기 혈액검사"),
            ("URINE_TEST", "소변검사"),
            ("EYE_EXAM", "안과검진"),
            ("APPOINTMENT", "외래 진료"),
            ("INJECTION", "주사 투여"),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "reminder_labels@example.com", "01093000003")
            for stype, label in type_to_label:
                await client.post(
                    SCHEDULES_EP,
                    json={**_BASE_PAYLOAD, "schedule_type": stype, "title": label, "scheduled_date": "2026-09-01"},
                    headers={"Authorization": f"Bearer {token}"},
                )
        user = await User.get(email="reminder_labels@example.com")
        notifs = await Notification.filter(user_id=user.id, notification_type=NotificationType.SCHEDULE).all()
        assert len(notifs) == 5
        title_to_notif = {n.title: n for n in notifs}
        for _, label in type_to_label:
            expected_title = f"[{label}] 일정 안내"
            assert expected_title in title_to_notif, f"title 없음: {expected_title}"
            notif = title_to_notif[expected_title]
            assert label in notif.content
            assert "2026-09-01" in notif.content

    async def test_content_contains_no_forbidden_medical_directives(self):
        """안전 문구 검증 — 해석·지시·권고 표현 미포함"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "reminder_safety@example.com", "01093000004")
            for stype in ["BLOOD_TEST", "URINE_TEST", "EYE_EXAM", "APPOINTMENT", "INJECTION"]:
                await client.post(
                    SCHEDULES_EP,
                    json={**_BASE_PAYLOAD, "schedule_type": stype, "title": stype, "scheduled_date": "2026-09-15"},
                    headers={"Authorization": f"Bearer {token}"},
                )
        user = await User.get(email="reminder_safety@example.com")
        notifs = await Notification.filter(user_id=user.id, notification_type=NotificationType.SCHEDULE).all()
        for notif in notifs:
            for word in FORBIDDEN_WORDS:
                assert word not in notif.title, f"금지어 '{word}' in title: {notif.title}"
                assert word not in notif.content, f"금지어 '{word}' in content: {notif.content}"

    async def test_notification_belongs_to_schedule_creator(self):
        """소유권 — 등록자 본인 알림에만 생성, 타 유저 알림 미생성"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "reminder_owner_a@example.com", "01093000005")
            await _signup_and_login(client, "reminder_owner_b@example.com", "01093000006")
            await client.post(
                SCHEDULES_EP,
                json={
                    **_BASE_PAYLOAD,
                    "schedule_type": "INJECTION",
                    "title": "주사 투여",
                    "scheduled_date": "2026-08-20",
                },
                headers={"Authorization": f"Bearer {token_a}"},
            )
        user_a = await User.get(email="reminder_owner_a@example.com")
        user_b = await User.get(email="reminder_owner_b@example.com")
        notifs_a = await Notification.filter(user_id=user_a.id, notification_type=NotificationType.SCHEDULE).all()
        notifs_b = await Notification.filter(user_id=user_b.id, notification_type=NotificationType.SCHEDULE).all()
        assert len(notifs_a) == 1
        assert len(notifs_b) == 0

    async def test_schedule_creation_returns_201_even_with_past_remind_date(self):
        """알림 생성(과거 remind_date)이 일정 생성 201 응답을 막지 않음"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "reminder_201@example.com", "01093000007")
            resp = await client.post(
                SCHEDULES_EP,
                json={
                    **_BASE_PAYLOAD,
                    "schedule_type": "EYE_EXAM",
                    "title": "안과 검진",
                    "scheduled_date": "2026-05-15",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["schedule_type"] == "EYE_EXAM"
        user = await User.get(email="reminder_201@example.com")
        notifs = await Notification.filter(user_id=user.id, notification_type=NotificationType.SCHEDULE).all()
        assert len(notifs) == 1
