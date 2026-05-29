from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.prompts import (
    PromptCreateRequest,
    PromptListResponse,
    PromptResponse,
    PromptUpdateRequest,
)
from app.models.prompts import PromptType
from app.models.users import User
from app.services.prompts import PromptService

prompt_router = APIRouter(prefix="/prompts", tags=["prompts"])


@prompt_router.get(
    "",
    response_model=PromptListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_prompts(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PromptService, Depends(PromptService)],
    prompt_type: PromptType | None = None,
) -> Response:
    result = await service.get_prompts(prompt_type)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@prompt_router.post(
    "",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt(
    request: PromptCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PromptService, Depends(PromptService)],
) -> Response:
    result = await service.create_prompt(data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


@prompt_router.patch(
    "/{prompt_id}",
    response_model=PromptResponse,
    status_code=status.HTTP_200_OK,
)
async def update_prompt(
    prompt_id: int,
    request: PromptUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PromptService, Depends(PromptService)],
) -> Response:
    result = await service.update_prompt(prompt_id=prompt_id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
