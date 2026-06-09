from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.users import AutoimmuneOnboardingStatusResponse, UserInfoResponse, UserUpdateRequest
from app.models.autoimmune_profile import AutoimmuneProfile
from app.models.user_consents import ConsentType, UserConsent
from app.models.user_disease import UserDisease
from app.models.users import User
from app.services.users import UserManageService

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def user_me_info(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    return Response(UserInfoResponse.model_validate(user).model_dump(), status_code=status.HTTP_200_OK)


@user_router.get(
    "/me/autoimmune-onboarding",
    response_model=AutoimmuneOnboardingStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_autoimmune_onboarding_status(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    consent_done = await UserConsent.filter(
        user_id=user.id, consent_type=ConsentType.MEDICAL_DATA, agreed=True
    ).exists()
    disease_done = await UserDisease.filter(user_id=user.id, deleted_at__isnull=True).exists()
    risk_profile_done = await AutoimmuneProfile.filter(user_id=user.id).exists()
    completed = consent_done and disease_done and risk_profile_done
    return Response(
        AutoimmuneOnboardingStatusResponse(
            consent_done=consent_done,
            disease_done=disease_done,
            risk_profile_done=risk_profile_done,
            completed=completed,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@user_router.patch("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def update_user_me_info(
    update_data: UserUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    updated_user = await user_manage_service.update_user(user=user, data=update_data)
    return Response(UserInfoResponse.model_validate(updated_user).model_dump(), status_code=status.HTTP_200_OK)
