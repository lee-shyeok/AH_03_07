from __future__ import annotations

from datetime import date, datetime

from app.core import config
from app.dtos.autoimmune_medical import (
    LabResultCreateRequest,
    LabResultUpdateRequest,
    MedicalScheduleCreateRequest,
    MedicalScheduleUpdateRequest,
)
from app.models.lab_result import LabResult
from app.models.medical_schedule import MedicalSchedule, MedicalScheduleType
from app.models.users import User


class MedicalScheduleService:
    async def create_schedule(self, user: User, data: MedicalScheduleCreateRequest) -> MedicalSchedule:
        return await MedicalSchedule.create(
            user=user,
            schedule_type=data.schedule_type,
            title=data.title,
            scheduled_date=data.scheduled_date,
            reminder_days_before=data.reminder_days_before,
            note=data.note,
        )

    async def list_schedules(
        self,
        user: User,
        schedule_type: MedicalScheduleType | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[MedicalSchedule]:
        qs = MedicalSchedule.filter(user=user, deleted_at=None)
        if schedule_type is not None:
            qs = qs.filter(schedule_type=schedule_type)
        if from_date is not None:
            qs = qs.filter(scheduled_date__gte=from_date)
        if to_date is not None:
            qs = qs.filter(scheduled_date__lte=to_date)
        return await qs.order_by("scheduled_date")

    async def get_schedule(self, user: User, schedule_id: int) -> MedicalSchedule | None:
        return await MedicalSchedule.get_or_none(id=schedule_id, user=user, deleted_at=None)

    async def update_schedule(
        self, user: User, schedule_id: int, data: MedicalScheduleUpdateRequest
    ) -> MedicalSchedule | None:
        schedule = await self.get_schedule(user, schedule_id)
        if schedule is None:
            return None
        schedule.schedule_type = data.schedule_type
        schedule.title = data.title
        schedule.scheduled_date = data.scheduled_date
        schedule.reminder_days_before = data.reminder_days_before
        schedule.note = data.note
        schedule.updated_at = datetime.now(config.TIMEZONE)
        await schedule.save(
            update_fields=["schedule_type", "title", "scheduled_date", "reminder_days_before", "note", "updated_at"]
        )
        return schedule

    async def delete_schedule(self, user: User, schedule_id: int) -> bool:
        schedule = await self.get_schedule(user, schedule_id)
        if schedule is None:
            return False
        schedule.deleted_at = datetime.now(config.TIMEZONE)
        await schedule.save(update_fields=["deleted_at"])
        return True


class LabResultService:
    async def create_result(self, user: User, data: LabResultCreateRequest) -> LabResult:
        return await LabResult.create(
            user=user,
            test_date=data.test_date,
            test_item=data.test_item,
            value=data.value,
            reference_range=data.reference_range,
            note=data.note,
        )

    async def list_results(self, user: User) -> list[LabResult]:
        return await LabResult.filter(user=user, deleted_at=None).order_by("-test_date")

    async def get_result(self, user: User, result_id: int) -> LabResult | None:
        return await LabResult.get_or_none(id=result_id, user=user, deleted_at=None)

    async def update_result(self, user: User, result_id: int, data: LabResultUpdateRequest) -> LabResult | None:
        result = await self.get_result(user, result_id)
        if result is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        update_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(result, field, value)
        result.updated_at = datetime.now(config.TIMEZONE)
        update_fields.append("updated_at")
        await result.save(update_fields=update_fields)
        return result

    async def delete_result(self, user: User, result_id: int) -> bool:
        result = await self.get_result(user, result_id)
        if result is None:
            return False
        result.deleted_at = datetime.now(config.TIMEZONE)
        await result.save(update_fields=["deleted_at"])
        return True
