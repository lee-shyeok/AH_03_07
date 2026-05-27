from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_log import ActivityLogResponse, ActivityLogUpsertRequest
from app.models.users import User
from app.services.autoimmune_log_service import ActivityLogService

activity_log_router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@activity_log_router.put("/{log_date}", response_model=ActivityLogResponse, status_code=status.HTTP_200_OK)
async def upsert_activity_log(
    log_date: date,
    body: ActivityLogUpsertRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityLogService, Depends(ActivityLogService)],
) -> Response:
    log = await service.upsert_log(user=user, log_date=log_date, data=body)
    return Response(ActivityLogResponse.model_validate(log).model_dump(), status_code=status.HTTP_200_OK)


@activity_log_router.get("", response_model=list[ActivityLogResponse], status_code=status.HTTP_200_OK)
async def list_activity_logs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityLogService, Depends(ActivityLogService)],
) -> Response:
    logs = await service.list_logs(user=user)
    return Response(
        [ActivityLogResponse.model_validate(log).model_dump() for log in logs],
        status_code=status.HTTP_200_OK,
    )


@activity_log_router.get("/{log_date}", response_model=ActivityLogResponse, status_code=status.HTTP_200_OK)
async def get_activity_log(
    log_date: date,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityLogService, Depends(ActivityLogService)],
) -> Response:
    log = await service.get_log_by_date(user=user, log_date=log_date)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity log not found.")
    return Response(ActivityLogResponse.model_validate(log).model_dump(), status_code=status.HTTP_200_OK)
