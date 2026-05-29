from uuid import UUID

from app.models.content_conversions import ContentConversion, ConversionType


class ContentConversionRepository:
    """콘텐츠 변환 DB 쿼리"""

    @staticmethod
    async def create(user_id: UUID, guide_id: UUID, conversion_type: ConversionType) -> ContentConversion:
        return await ContentConversion.create(
            user_id=user_id,
            guide_id=guide_id,
            conversion_type=conversion_type,
        )

    @staticmethod
    async def get_by_id(conversion_id: UUID) -> ContentConversion | None:
        return await ContentConversion.filter(id=conversion_id).first()

    @staticmethod
    async def get_user_conversions(user_id: UUID) -> list[ContentConversion]:
        return await ContentConversion.filter(user_id=user_id).order_by("-created_at").all()
