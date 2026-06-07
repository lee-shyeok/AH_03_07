from __future__ import annotations

from datetime import date, datetime

from app.core import config
from app.dtos.lupus_daily_context import LupusDailyContextUpsertRequest
from app.models.lupus_daily_context import LupusDailyContext
from app.models.users import User


class LupusDailyContextService:
    async def upsert(self, user: User, data: LupusDailyContextUpsertRequest) -> LupusDailyContext:
        log = await LupusDailyContext.get_or_none(user=user, log_date=data.log_date)
        if log is None:
            return await LupusDailyContext.create(
                user=user,
                log_date=data.log_date,
                uv_exposure_minutes=data.uv_exposure_minutes,
                sleep_hours=data.sleep_hours,
                stress_level=data.stress_level,
                med_taken=data.med_taken,
                note=data.note,
            )
        log.uv_exposure_minutes = data.uv_exposure_minutes
        log.sleep_hours = data.sleep_hours
        log.stress_level = data.stress_level
        log.med_taken = data.med_taken
        log.note = data.note
        log.updated_at = datetime.now(config.TIMEZONE)
        await log.save(
            update_fields=[
                "uv_exposure_minutes",
                "sleep_hours",
                "stress_level",
                "med_taken",
                "note",
                "updated_at",
            ]
        )
        return log

    async def get_by_date(self, user: User, log_date: date) -> LupusDailyContext | None:
        return await LupusDailyContext.get_or_none(user=user, log_date=log_date)
