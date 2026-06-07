from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.lupus_daily_context import (
    LupusDailyContextResponse,
    LupusDailyContextUpsertRequest,
)
from app.models.users import User
from app.services.lupus_daily_context_service import LupusDailyContextService

lupus_daily_context_router = APIRouter(prefix="/lupus-daily-context", tags=["lupus-daily-context"])


@lupus_daily_context_router.post("", response_model=LupusDailyContextResponse, status_code=status.HTTP_200_OK)
async def upsert_lupus_daily_context(
    body: LupusDailyContextUpsertRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusDailyContextService, Depends(LupusDailyContextService)],
) -> Response:
    log = await service.upsert(user=user, data=body)
    return Response(LupusDailyContextResponse.model_validate(log).model_dump(), status_code=status.HTTP_200_OK)


@lupus_daily_context_router.get("/{log_date}", response_model=LupusDailyContextResponse, status_code=status.HTTP_200_OK)
async def get_lupus_daily_context(
    log_date: date,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusDailyContextService, Depends(LupusDailyContextService)],
) -> Response:
    log = await service.get_by_date(user=user, log_date=log_date)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lupus daily context not found.")
    return Response(LupusDailyContextResponse.model_validate(log).model_dump(), status_code=status.HTTP_200_OK)
