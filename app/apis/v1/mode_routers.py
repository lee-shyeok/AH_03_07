from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.autoimmune import ModeResponse, ModeUpdateRequest
from app.models.users import User
from app.services.autoimmune_service import ModeService

mode_router = APIRouter(prefix="/users/me", tags=["mode"])


@mode_router.get("/mode", response_model=ModeResponse, status_code=status.HTTP_200_OK)
async def get_mode(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    return Response(ModeResponse.model_validate(user).model_dump(), status_code=status.HTTP_200_OK)


@mode_router.patch("/mode", response_model=ModeResponse, status_code=status.HTTP_200_OK)
async def update_mode(
    body: ModeUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ModeService, Depends(ModeService)],
) -> Response:
    updated_user = await service.update_mode(user=user, new_mode=body.mode)
    return Response(ModeResponse.model_validate(updated_user).model_dump(), status_code=status.HTTP_200_OK)
