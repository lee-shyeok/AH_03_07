from uuid import UUID

from app.models.medical_appointments import MedicalAppointment
from app.models.favorite_places import FavoritePlace, PlaceType


class ScheduleRepository:
    """일정 관리 DB 쿼리"""

    @staticmethod
    async def create_appointment(user_id: UUID, **kwargs) -> MedicalAppointment:
        return await MedicalAppointment.create(user_id=user_id, **kwargs)

    @staticmethod
    async def get_user_appointments(user_id: UUID) -> list[MedicalAppointment]:
        return await MedicalAppointment.filter(user_id=user_id).order_by("appointment_date").all()

    @staticmethod
    async def create_favorite_place(user_id: UUID, **kwargs) -> FavoritePlace:
        return await FavoritePlace.create(user_id=user_id, **kwargs)

    @staticmethod
    async def get_user_favorite_places(user_id: UUID, place_type: PlaceType | None = None) -> list[FavoritePlace]:
        if place_type:
            return await FavoritePlace.filter(user_id=user_id, place_type=place_type).all()
        return await FavoritePlace.filter(user_id=user_id).all()
