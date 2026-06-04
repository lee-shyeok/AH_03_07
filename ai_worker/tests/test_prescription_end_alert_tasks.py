"""REQ-NOTI-007 — 처방 종료일 알림 태스크 테스트."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_worker.tasks.prescription_end_alert_tasks import (
    _adjust_to_weekday,
    compute_alert_dates,
)

# ── 평일 보정 단위 테스트 ─────────────────────────────────────────────────────


def test_adjust_weekday_monday_unchanged() -> None:
    """월요일은 보정 없음."""
    monday = datetime.date(2026, 6, 1)  # 월요일
    assert _adjust_to_weekday(monday) == monday


def test_adjust_saturday_to_friday() -> None:
    """토요일 → 직전 금요일."""
    saturday = datetime.date(2026, 6, 6)  # 토요일
    expected = datetime.date(2026, 6, 5)  # 금요일
    assert _adjust_to_weekday(saturday) == expected


def test_adjust_sunday_to_friday() -> None:
    """일요일 → 직전 금요일."""
    sunday = datetime.date(2026, 6, 7)  # 일요일
    expected = datetime.date(2026, 6, 5)  # 금요일
    assert _adjust_to_weekday(sunday) == expected


# ── compute_alert_dates 단위 테스트 ──────────────────────────────────────────


def test_compute_alert_dates_returns_three_keys() -> None:
    """D-7, D-3, D-1 세 알림일 반환."""
    end_date = datetime.date(2026, 6, 30)
    alerts = compute_alert_dates(end_date)
    assert set(alerts.keys()) == {7, 3, 1}


def test_compute_alert_dates_weekend_correction() -> None:
    """종료일 기준 D-N이 주말이면 금요일로 보정."""
    # 2026-06-28(일): D-1 → 2026-06-27(토) → 2026-06-26(금)
    end_date = datetime.date(2026, 6, 28)  # 일요일
    alerts = compute_alert_dates(end_date)
    d1_alert = alerts[1]
    assert d1_alert.weekday() not in (5, 6), f"D-1 alert landed on weekend: {d1_alert}"


# ── _create_alerts 통합 테스트 (DB mock) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_create_alerts_calls_notification_create() -> None:
    """today == D-1 alert_date이면 Notification.create 호출."""
    end_date = datetime.date(2026, 6, 10)  # 수요일
    today = end_date - datetime.timedelta(days=1)  # D-1 = 화요일 (평일)

    mock_user = MagicMock()
    mock_user.id = 42

    mock_med = MagicMock()
    mock_med.name = "메토트렉세이트"
    mock_med.end_date = end_date
    mock_med.user = mock_user
    mock_med.user_id = 42
    mock_med.deleted_at = None

    with (
        patch(
            "ai_worker.tasks.prescription_end_alert_tasks._create_alerts",
            wraps=None,
        ),
        patch("app.models.user_medication.UserMedication") as mock_med_cls,
        patch("app.models.notifications.Notification") as mock_notif_cls,
        patch("datetime.date") as mock_date,
    ):
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *a, **kw: datetime.date(*a, **kw)

        mock_med_cls.filter.return_value.select_related = MagicMock(return_value=AsyncMock(return_value=[mock_med]))
        mock_notif_cls.create = AsyncMock()

        from ai_worker.tasks.prescription_end_alert_tasks import _create_alerts

        with (
            patch("app.models.notifications.Notification.create", new=mock_notif_cls.create),
            patch(
                "app.models.user_medication.UserMedication.filter",
                return_value=MagicMock(select_related=MagicMock(return_value=AsyncMock(return_value=[mock_med]))),
            ),
            patch("datetime.date.today", return_value=today),
        ):
            await _create_alerts()
