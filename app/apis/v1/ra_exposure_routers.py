from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.ra_exposure import RAExposureResponse
from app.models.users import User
from app.services.ra_exposure_service import RAExposureService

ra_exposure_router = APIRouter(
    prefix="/ra-exposure-triggers",
    tags=["ra-exposure-triggers"],
)


@ra_exposure_router.get(
    "",
    response_class=ORJSONResponse,
    status_code=status.HTTP_200_OK,
    response_model=RAExposureResponse,
)
async def get_ra_exposure_triggers(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RAExposureService, Depends(RAExposureService)],
) -> ORJSONResponse:
    result = await service.evaluate(user)
    return ORJSONResponse(content=result.model_dump(mode="json"))
