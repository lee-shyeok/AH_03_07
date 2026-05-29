from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.notifications import (
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdateRequest,
)
from app.models.users import User
from app.services.notifications import NotificationService

notification_router = APIRouter(prefix="/notifications", tags=["notifications"])


# ========== 알림 설정 ==========


@notification_router.get(
    "/settings",
    response_model=NotificationSettingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_notification_setting(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    """내 알림 설정 조회"""
    result = await service.get_my_setting(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@notification_router.patch(
    "/settings",
    response_model=NotificationSettingResponse,
    status_code=status.HTTP_200_OK,
)
async def update_my_notification_setting(
    request: NotificationSettingUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    """내 알림 설정 수정"""
    result = await service.update_my_setting(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


# ========== 알림 ==========


@notification_router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_notifications(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    """내 알림 목록 조회"""
    result = await service.get_my_notifications(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@notification_router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_notification_as_read(
    notification_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    """알림 읽음 처리"""
    result = await service.mark_as_read(user_id=user.id, notification_id=notification_id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
