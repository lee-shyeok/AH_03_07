from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_medical import (
    MedicalScheduleCreateRequest,
    MedicalScheduleResponse,
    MedicalScheduleUpdateRequest,
)
from app.models.medical_schedule import MedicalScheduleType
from app.models.users import User
from app.services.autoimmune_medical_service import MedicalScheduleService
from app.services.schedule_reminder_service import ScheduleReminderService

medical_schedule_router = APIRouter(prefix="/care-schedules", tags=["care-schedules"])


@medical_schedule_router.post("", response_model=MedicalScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_schedule(
    body: MedicalScheduleCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalScheduleService, Depends(MedicalScheduleService)],
    reminder_service: Annotated[ScheduleReminderService, Depends(ScheduleReminderService)],
) -> ORJSONResponse:
    schedule = await service.create_schedule(user=user, data=body)
    await reminder_service.create_reminder_for_schedule(schedule)
    return ORJSONResponse(
        MedicalScheduleResponse.model_validate(schedule).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@medical_schedule_router.get("", response_model=list[MedicalScheduleResponse], status_code=status.HTTP_200_OK)
async def list_medical_schedules(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalScheduleService, Depends(MedicalScheduleService)],
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    schedule_type: MedicalScheduleType | None = Query(default=None, alias="type"),
) -> ORJSONResponse:
    schedules = await service.list_schedules(
        user=user, schedule_type=schedule_type, from_date=from_date, to_date=to_date
    )
    return ORJSONResponse(
        [MedicalScheduleResponse.model_validate(s).model_dump() for s in schedules],
        status_code=status.HTTP_200_OK,
    )


@medical_schedule_router.put("/{schedule_id}", response_model=MedicalScheduleResponse, status_code=status.HTTP_200_OK)
async def update_medical_schedule(
    schedule_id: int,
    body: MedicalScheduleUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalScheduleService, Depends(MedicalScheduleService)],
) -> ORJSONResponse:
    schedule = await service.update_schedule(user=user, schedule_id=schedule_id, data=body)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical schedule not found.")
    return ORJSONResponse(
        MedicalScheduleResponse.model_validate(schedule).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@medical_schedule_router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_schedule(
    schedule_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicalScheduleService, Depends(MedicalScheduleService)],
) -> Response:
    deleted = await service.delete_schedule(user=user, schedule_id=schedule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical schedule not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
