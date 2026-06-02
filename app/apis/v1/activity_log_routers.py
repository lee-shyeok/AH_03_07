from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_alert import ActivityChartResponse, ChartPeriod
from app.dtos.autoimmune_log import ActivityLogResponse, ActivityLogUpsertRequest
from app.models.users import User
from app.services.autoimmune_alert_service import ActivityChartService
from app.services.autoimmune_log_service import ActivityLogService

activity_log_router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@activity_log_router.post("", response_model=ActivityLogResponse, status_code=status.HTTP_200_OK)
async def upsert_activity_log(
    body: ActivityLogUpsertRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityLogService, Depends(ActivityLogService)],
) -> Response:
    log = await service.upsert_log(user=user, data=body)
    return Response(ActivityLogResponse.model_validate(log).model_dump(), status_code=status.HTTP_200_OK)


@activity_log_router.get("", response_model=list[ActivityLogResponse], status_code=status.HTTP_200_OK)
async def list_activity_logs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityLogService, Depends(ActivityLogService)],
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> Response:
    logs = await service.list_logs(user=user, from_date=from_date, to_date=to_date)
    return Response(
        [ActivityLogResponse.model_validate(log).model_dump() for log in logs],
        status_code=status.HTTP_200_OK,
    )


@activity_log_router.get("/chart", response_model=ActivityChartResponse, status_code=status.HTTP_200_OK)
async def get_activity_chart(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ActivityChartService, Depends(ActivityChartService)],
    period: ChartPeriod = ChartPeriod.WEEK,
) -> Response:
    chart = await service.get_chart(user=user, period=period)
    return Response(chart.model_dump(), status_code=status.HTTP_200_OK)


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
