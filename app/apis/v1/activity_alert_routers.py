from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_alert import (
    AlertSettingResponse,
    AlertSettingUpsertRequest,
    AlertStatusResponse,
    AlertTemplatesResponse,
)
from app.models.users import User
from app.services.autoimmune_alert_service import ActivityAlertService

activity_alert_router = APIRouter(prefix="/activity-alerts", tags=["activity-alerts"])


@activity_alert_router.put("/setting", response_model=AlertSettingResponse, status_code=status.HTTP_200_OK)
async def upsert_alert_setting(
    body: AlertSettingUpsertRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityAlertService, Depends(ActivityAlertService)],
) -> Response:
    setting = await service.upsert_setting(user=user, data=body)
    return Response(AlertSettingResponse.model_validate(setting).model_dump(), status_code=status.HTTP_200_OK)


@activity_alert_router.get("/setting", response_model=AlertSettingResponse, status_code=status.HTTP_200_OK)
async def get_alert_setting(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityAlertService, Depends(ActivityAlertService)],
) -> Response:
    setting = await service.get_setting(user=user)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert setting not found.")
    return Response(AlertSettingResponse.model_validate(setting).model_dump(), status_code=status.HTTP_200_OK)


@activity_alert_router.get("/status", response_model=AlertStatusResponse, status_code=status.HTTP_200_OK)
async def get_alert_status(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityAlertService, Depends(ActivityAlertService)],
) -> Response:
    alert_status = await service.get_status(user=user)
    return Response(alert_status.model_dump(), status_code=status.HTTP_200_OK)


@activity_alert_router.get("/templates", response_model=AlertTemplatesResponse, status_code=status.HTTP_200_OK)
async def get_alert_templates(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityAlertService, Depends(ActivityAlertService)],
) -> Response:
    templates = service.get_templates()
    return Response(AlertTemplatesResponse(templates=templates).model_dump(), status_code=status.HTTP_200_OK)
