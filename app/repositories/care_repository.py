from uuid import UUID

from app.models.share_links import ShareLink
from app.models.share_logs import ShareLog
from app.models.guardians import Guardian


class CareRepository:
    """보호자 공유 DB 쿼리"""

    @staticmethod
    async def create_guardian(user_id: UUID, **kwargs) -> Guardian:
        return await Guardian.create(user_id=user_id, **kwargs)

    @staticmethod
    async def get_user_guardians(user_id: UUID) -> list[Guardian]:
        return await Guardian.filter(user_id=user_id, is_active=True).all()

    @staticmethod
    async def create_share_link(user_id: UUID, **kwargs) -> ShareLink:
        return await ShareLink.create(user_id=user_id, **kwargs)

    @staticmethod
    async def get_user_share_links(user_id: UUID) -> list[ShareLink]:
        return await ShareLink.filter(user_id=user_id).order_by("-created_at").all()

    @staticmethod
    async def get_share_link_by_token(token: str) -> ShareLink | None:
        return await ShareLink.filter(token=token, is_revoked=False).first()

    @staticmethod
    async def revoke_share_link(link_id: UUID) -> ShareLink | None:
        link = await ShareLink.filter(id=link_id).first()
        if link:
            link.is_revoked = True
            await link.save()
        return link

    @staticmethod
    async def log_share_access(share_link_id: UUID, viewer_ip: str | None = None) -> ShareLog:
        return await ShareLog.create(share_link_id=share_link_id, viewer_ip=viewer_ip)
