from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.lupus_exposure import LupusExposureResponse
from app.models.users import User
from app.services.lupus_exposure_service import LupusExposureService

lupus_exposure_router = APIRouter(
    prefix="/lupus-exposure-triggers",
    tags=["lupus-exposure-triggers"],
)


@lupus_exposure_router.get(
    "",
    response_class=ORJSONResponse,
    status_code=status.HTTP_200_OK,
    response_model=LupusExposureResponse,
)
async def get_lupus_exposure_triggers(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusExposureService, Depends(LupusExposureService)],
) -> ORJSONResponse:
    result = await service.evaluate(user)
    return ORJSONResponse(content=result.model_dump(mode="json"))
