from __future__ import annotations

from datetime import datetime, timedelta

from app.core import config
from app.dtos.autoimmune_alert import (
    ActivityChartPoint,
    ActivityChartResponse,
    AlertSettingUpsertRequest,
    AlertStatusResponse,
    ChartPeriod,
    MetricStats,
)
from app.models.activity_alert_setting import ActivityAlertSetting, AlertCriterion
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.users import User

# NFR-SAFE-001 — 사용자 자가 설정 알림 면책 문구
ALERT_DISCLAIMER = "본 알림은 사용자가 직접 설정한 자가 모니터링 알림입니다. 의학적 판단은 담당 의료진에게 문의하세요."

# §27 검수된 정형 템플릿 — 평가·단정 표현 없음
DEFAULT_ALERT_TEMPLATES = [
    "기록한 수치를 다음 진료 시 의료진과 공유하세요",
    "오늘은 컨디션을 의료진과 공유하기 좋을 것 같아요",
    "담당 의료진 상담을 권고합니다",
]

_PERIOD_DAYS = {ChartPeriod.WEEK: 7, ChartPeriod.MONTH: 30, ChartPeriod.QUARTER: 90}


class ActivityChartService:
    async def get_chart(self, user: User, period: ChartPeriod) -> ActivityChartResponse:
        today = datetime.now(config.TIMEZONE).date()
        days = _PERIOD_DAYS[period]
        start = today - timedelta(days=days - 1)
        end = today

        logs = await DiseaseActivityLog.filter(user=user, log_date__gte=start, log_date__lte=end).order_by("log_date")

        series = [ActivityChartPoint(log_date=log.log_date, pain_vas=log.pain_vas, fatigue=log.fatigue) for log in logs]

        if logs:
            pain_vals = [log.pain_vas for log in logs]
            fatigue_vals = [log.fatigue for log in logs]
            pain_stats = MetricStats(
                avg=round(sum(pain_vals) / len(pain_vals), 1),
                max=max(pain_vals),
                min=min(pain_vals),
            )
            fatigue_stats = MetricStats(
                avg=round(sum(fatigue_vals) / len(fatigue_vals), 1),
                max=max(fatigue_vals),
                min=min(fatigue_vals),
            )
        else:
            pain_stats = MetricStats(avg=None, max=None, min=None)
            fatigue_stats = MetricStats(avg=None, max=None, min=None)

        return ActivityChartResponse(
            period=period,
            start_date=start,
            end_date=end,
            series=series,
            pain_stats=pain_stats,
            fatigue_stats=fatigue_stats,
        )


class ActivityAlertService:
    async def upsert_setting(self, user: User, data: AlertSettingUpsertRequest) -> ActivityAlertSetting:
        setting = await ActivityAlertSetting.get_or_none(user=user)
        if setting is None:
            return await ActivityAlertSetting.create(
                user=user,
                pain_threshold=data.pain_threshold,
                pain_consecutive_days=data.pain_consecutive_days,
                morning_stiffness_threshold=data.morning_stiffness_threshold,
                fatigue_threshold=data.fatigue_threshold,
                alert_message=data.alert_message,
                is_enabled=data.is_enabled,
            )
        update_data = data.model_dump()
        update_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(setting, field, value)
        setting.updated_at = datetime.now(config.TIMEZONE)
        update_fields.append("updated_at")
        await setting.save(update_fields=update_fields)
        return setting

    async def get_setting(self, user: User) -> ActivityAlertSetting | None:
        return await ActivityAlertSetting.get_or_none(user=user)

    async def get_status(self, user: User) -> AlertStatusResponse:
        setting = await ActivityAlertSetting.get_or_none(user=user)

        if setting is None or not setting.is_enabled:
            return AlertStatusResponse(
                is_enabled=setting.is_enabled if setting else False,
                triggered=False,
                triggered_criteria=[],
                alert_message=None,
                disclaimer=None,
            )

        n_needed = max(setting.pain_consecutive_days or 1, 1)
        recent_logs = await DiseaseActivityLog.filter(user=user).order_by("-log_date").limit(n_needed)

        triggered_criteria: list[AlertCriterion] = []

        if setting.pain_threshold is not None:
            n = setting.pain_consecutive_days or 1
            if len(recent_logs) >= n and all(log.pain_vas >= setting.pain_threshold for log in recent_logs[:n]):
                triggered_criteria.append(AlertCriterion.PAIN)

        if setting.morning_stiffness_threshold is not None and recent_logs:
            latest = recent_logs[0]
            if (
                latest.morning_stiffness_min is not None
                and latest.morning_stiffness_min >= setting.morning_stiffness_threshold
            ):
                triggered_criteria.append(AlertCriterion.MORNING_STIFFNESS)

        if setting.fatigue_threshold is not None and recent_logs:
            if recent_logs[0].fatigue >= setting.fatigue_threshold:
                triggered_criteria.append(AlertCriterion.FATIGUE)

        triggered = bool(triggered_criteria)
        return AlertStatusResponse(
            is_enabled=True,
            triggered=triggered,
            triggered_criteria=triggered_criteria,
            alert_message=setting.alert_message if triggered else None,
            disclaimer=ALERT_DISCLAIMER if triggered else None,
        )

    def get_templates(self) -> list[str]:
        return DEFAULT_ALERT_TEMPLATES
