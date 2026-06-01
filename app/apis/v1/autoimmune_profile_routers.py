from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_profile import (
    AutoimmuneProfilePutResponse,
    AutoimmuneProfileResponse,
    AutoimmuneProfileUpsertRequest,
)
from app.models.autoimmune_profile import AutoimmunePregnancyStatus, AutoimmuneProfile
from app.models.users import User
from app.services.autoimmune_profile_service import AutoimmuneProfileService

autoimmune_profile_router = APIRouter(prefix="/autoimmune", tags=["autoimmune-profile"])

_DEFAULT_PROFILE = AutoimmuneProfileResponse(
    risk_factors={},
    pregnancy_status=AutoimmunePregnancyStatus.NONE,
    vaccination_history=[],
)


@autoimmune_profile_router.get(
    "/profile",
    response_model=AutoimmuneProfileResponse,
)
async def get_autoimmune_profile(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[AutoimmuneProfileService, Depends(AutoimmuneProfileService)],
) -> AutoimmuneProfileResponse:
    profile = await service.get_profile(user=user)
    if profile is None:
        return _DEFAULT_PROFILE
    return AutoimmuneProfileResponse.model_validate(profile)


@autoimmune_profile_router.put(
    "/profile",
    response_model=AutoimmuneProfilePutResponse,
)
async def upsert_autoimmune_profile(
    body: AutoimmuneProfileUpsertRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[AutoimmuneProfileService, Depends(AutoimmuneProfileService)],
) -> AutoimmuneProfilePutResponse:
    profile: AutoimmuneProfile = await service.upsert_profile(user=user, data=body)
    return AutoimmuneProfilePutResponse(
        risk_factors=profile.risk_factors,
        pregnancy_status=profile.pregnancy_status,
        vaccination_history=profile.vaccination_history,
        advisory_message=service.advisory_message(profile),
    )
