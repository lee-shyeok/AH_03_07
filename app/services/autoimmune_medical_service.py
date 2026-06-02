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
            test_item=data.test_type,
            value=data.user_recorded_value,
            reference_range=data.reference_range,
            note=data.note,
        )

    async def list_results(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LabResult]:
        qs = LabResult.filter(user=user, deleted_at=None)
        if from_date is not None:
            qs = qs.filter(test_date__gte=from_date)
        if to_date is not None:
            qs = qs.filter(test_date__lte=to_date)
        return await qs.order_by("-test_date")

    async def get_result(self, user: User, result_id: int) -> LabResult | None:
        return await LabResult.get_or_none(id=result_id, user=user, deleted_at=None)

    async def update_result(self, user: User, result_id: int, data: LabResultUpdateRequest) -> LabResult | None:
        result = await self.get_result(user, result_id)
        if result is None:
            return None
        # DTO field name → model column name mapping (PATCH: only set fields explicitly sent)
        field_map: list[tuple[str, str]] = [
            ("test_date", "test_date"),
            ("test_type", "test_item"),
            ("user_recorded_value", "value"),
            ("reference_range", "reference_range"),
            ("note", "note"),
        ]
        update_fields: list[str] = []
        for dto_field, model_field in field_map:
            if dto_field in data.model_fields_set:
                setattr(result, model_field, getattr(data, dto_field))
                update_fields.append(model_field)
        if update_fields:
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
