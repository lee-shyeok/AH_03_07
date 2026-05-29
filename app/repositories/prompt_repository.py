from uuid import UUID

from app.models.prompts import Prompt, PromptType


class PromptRepository:
    @staticmethod
    async def get_all(prompt_type: PromptType | None = None) -> list[Prompt]:
        if prompt_type:
            return await Prompt.filter(prompt_type=prompt_type).order_by("-created_at").all()
        return await Prompt.all().order_by("-created_at")

    @staticmethod
    async def get_active(prompt_type: PromptType) -> Prompt | None:
        return await Prompt.filter(prompt_type=prompt_type, is_active=True).order_by("-created_at").first()

    @staticmethod
    async def get_by_id(prompt_id: UUID) -> Prompt | None:
        return await Prompt.filter(id=prompt_id).first()

    @staticmethod
    async def create(**kwargs) -> Prompt:
        return await Prompt.create(**kwargs)

    @staticmethod
    async def update(prompt_id: int, **kwargs) -> Prompt | None:
        prompt = await Prompt.filter(id=prompt_id).first()
        if prompt:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(prompt, key, value)
            await prompt.save()
        return prompt
