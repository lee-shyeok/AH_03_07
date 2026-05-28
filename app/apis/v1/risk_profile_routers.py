from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_profile import RiskProfileResponse, RiskProfileUpsertRequest
from app.models.users import User
from app.services.autoimmune_profile_service import RiskProfileService

risk_profile_router = APIRouter(prefix="/users/me/risk-profile", tags=["risk-profile"])


@risk_profile_router.get("", response_model=RiskProfileResponse, status_code=status.HTTP_200_OK)
async def get_risk_profile(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RiskProfileService, Depends(RiskProfileService)],
) -> Response:
    profile = await service.get_profile(user=user)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk profile not found.")
    return Response(RiskProfileResponse.model_validate(profile).model_dump(), status_code=status.HTTP_200_OK)


@risk_profile_router.put("", response_model=RiskProfileResponse, status_code=status.HTTP_200_OK)
async def upsert_risk_profile(
    body: RiskProfileUpsertRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RiskProfileService, Depends(RiskProfileService)],
) -> Response:
    profile = await service.upsert_profile(user=user, data=body)
    return Response(RiskProfileResponse.model_validate(profile).model_dump(), status_code=status.HTTP_200_OK)
