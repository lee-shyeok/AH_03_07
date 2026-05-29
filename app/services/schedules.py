from datetime import timedelta
from uuid import UUID

from app.dtos.schedules import (
    AppointmentCreateRequest,
    AppointmentListResponse,
    AppointmentResponse,
    FavoritePlaceCreateRequest,
    FavoritePlaceListResponse,
    FavoritePlaceResponse,
)
from app.models.favorite_places import PlaceType
from app.models.notifications import NotificationType
from app.repositories.notification_repository import NotificationRepository
from app.repositories.schedule_repository import ScheduleRepository


class ScheduleService:
    """일정 관리 비즈니스 로직"""

    def __init__(self):
        self.repo = ScheduleRepository()
        self.noti_repo = NotificationRepository()

    async def create_appointment(self, user_id: UUID, data: AppointmentCreateRequest) -> AppointmentResponse:
        """진료 예약 등록 + 자동 알림 예약"""
        appointment = await self.repo.create_appointment(
            user_id=user_id,
            appointment_date=data.appointment_date,
            hospital_name=data.hospital_name,
            doctor_name=data.doctor_name,
            purpose=data.purpose,
            notes=data.notes,
            notification_enabled=data.notification_enabled,
        )

        # 자동 알림 예약 (1주 전, 1일 전)
        if data.notification_enabled:
            try:
                one_week_before = data.appointment_date - timedelta(days=7)
                one_day_before = data.appointment_date - timedelta(days=1)

                await self.noti_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.MEDICATION,
                    title="진료 1주일 전 안내",
                    content=f"{data.hospital_name} 진료가 1주일 후 예정되어 있습니다.",
                    scheduled_at=one_week_before,
                )

                await self.noti_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.MEDICATION,
                    title="내일 진료 예정",
                    content=f"내일 {data.hospital_name} 진료가 예정되어 있습니다. 진료 동행 PDF를 준비하시겠어요?",
                    scheduled_at=one_day_before,
                )
            except Exception as err:
                print(f"진료 알림 예약 실패: {err}")

        return AppointmentResponse.model_validate(appointment)

    async def get_my_appointments(self, user_id: UUID) -> AppointmentListResponse:
        """내 진료 일정 목록"""
        appointments = await self.repo.get_user_appointments(user_id)
        return AppointmentListResponse(
            appointments=[AppointmentResponse.model_validate(a) for a in appointments],
            total=len(appointments),
        )

    async def create_favorite_place(self, user_id: UUID, data: FavoritePlaceCreateRequest) -> FavoritePlaceResponse:
        """단골 병원/약국 등록"""
        place = await self.repo.create_favorite_place(
            user_id=user_id,
            place_type=data.place_type,
            name=data.name,
            address=data.address,
            phone=data.phone,
            memo=data.memo,
        )
        return FavoritePlaceResponse.model_validate(place)

    async def get_my_favorite_places(
        self, user_id: UUID, place_type: PlaceType | None = None
    ) -> FavoritePlaceListResponse:
        """단골 병원/약국 목록"""
        places = await self.repo.get_user_favorite_places(user_id, place_type)
        return FavoritePlaceListResponse(
            places=[FavoritePlaceResponse.model_validate(p) for p in places],
            total=len(places),
        )
