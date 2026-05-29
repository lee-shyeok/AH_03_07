from fastapi import HTTPException, status

from app.dtos.prompts import (
    PromptCreateRequest,
    PromptListResponse,
    PromptResponse,
    PromptUpdateRequest,
)
from app.models.prompts import PromptType
from app.repositories.prompt_repository import PromptRepository


class PromptService:
    def __init__(self):
        self.repo = PromptRepository()

    async def get_prompts(self, prompt_type: PromptType | None = None) -> PromptListResponse:
        prompts = await self.repo.get_all(prompt_type)
        return PromptListResponse(
            prompts=[PromptResponse.model_validate(p) for p in prompts],
            total=len(prompts),
        )

    async def create_prompt(self, data: PromptCreateRequest) -> PromptResponse:
        prompt = await self.repo.create(
            prompt_type=data.prompt_type,
            name=data.name,
            version=data.version,
            template_text=data.template_text,
            variables=data.variables,
            is_active=data.is_active,
        )
        return PromptResponse.model_validate(prompt)

    async def update_prompt(self, prompt_id: int, data: PromptUpdateRequest) -> PromptResponse:
        prompt = await self.repo.get_by_id(prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="프롬프트를 찾을 수 없습니다.",
            )

        updated = await self.repo.update(
            prompt_id=prompt_id,
            name=data.name,
            template_text=data.template_text,
            variables=data.variables,
            is_active=data.is_active,
        )
        return PromptResponse.model_validate(updated)
