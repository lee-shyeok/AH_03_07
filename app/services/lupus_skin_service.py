from __future__ import annotations

from datetime import datetime

from app.core import config
from app.dtos.lupus_skin import LupusSkinLogCreateRequest, LupusSkinLogUpdateRequest
from app.models.lupus_skin_log import LupusSkinLog
from app.models.users import User


class LupusSkinLogService:
    async def create_log(self, user: User, data: LupusSkinLogCreateRequest) -> LupusSkinLog:
        return await LupusSkinLog.create(user=user, **data.model_dump())

    async def list_logs(self, user: User) -> list[LupusSkinLog]:
        return await LupusSkinLog.filter(user=user, deleted_at=None).order_by("-log_date")

    async def get_log(self, user: User, log_id: int) -> LupusSkinLog | None:
        return await LupusSkinLog.get_or_none(id=log_id, user=user, deleted_at=None)

    async def update_log(self, user: User, log_id: int, data: LupusSkinLogUpdateRequest) -> LupusSkinLog | None:
        log = await self.get_log(user, log_id)
        if log is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        update_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(log, field, value)
        if update_fields:
            log.updated_at = datetime.now(config.TIMEZONE)
            update_fields.append("updated_at")
            await log.save(update_fields=update_fields)
        return log

    async def delete_log(self, user: User, log_id: int) -> bool:
        log = await self.get_log(user, log_id)
        if log is None:
            return False
        log.deleted_at = datetime.now(config.TIMEZONE)
        await log.save(update_fields=["deleted_at"])
        return True
