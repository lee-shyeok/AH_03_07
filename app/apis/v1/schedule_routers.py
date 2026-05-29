from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.security import get_request_user
from app.dtos.schedules import (
    AppointmentCreateRequest,
    AppointmentListResponse,
    AppointmentResponse,
    FavoritePlaceCreateRequest,
    FavoritePlaceListResponse,
    FavoritePlaceResponse,
)
from app.models.favorite_places import PlaceType
from app.models.users import User
from app.services.schedules import ScheduleService

schedule_router = APIRouter(prefix="/schedules", tags=["schedules"])


@schedule_router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """진료 예약 등록"""
    service = ScheduleService()
    return await service.create_appointment(user.id, data)


@schedule_router.get("/appointments", response_model=AppointmentListResponse)
async def get_my_appointments(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 진료 일정 목록"""
    service = ScheduleService()
    return await service.get_my_appointments(user.id)


@schedule_router.post("/favorite-places", response_model=FavoritePlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite_place(
    data: FavoritePlaceCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """단골 병원/약국 등록"""
    service = ScheduleService()
    return await service.create_favorite_place(user.id, data)


@schedule_router.get("/favorite-places", response_model=FavoritePlaceListResponse)
async def get_my_favorite_places(
    user: Annotated[User, Depends(get_request_user)],
    place_type: Annotated[PlaceType | None, Query()] = None,
):
    """단골 병원/약국 목록"""
    service = ScheduleService()
    return await service.get_my_favorite_places(user.id, place_type)
