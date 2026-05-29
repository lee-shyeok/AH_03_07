import secrets
from datetime import datetime, timedelta
from uuid import UUID

from app.dtos.care import (
    GuardianCreateRequest,
    GuardianListResponse,
    GuardianResponse,
    ShareLinkCreateRequest,
    ShareLinkListResponse,
    ShareLinkResponse,
)
from app.models.share_links import ShareDuration
from app.repositories.care_repository import CareRepository


class CareService:
    """보호자 공유 비즈니스 로직"""

    def __init__(self):
        self.repo = CareRepository()

    async def create_guardian(self, user_id: UUID, data: GuardianCreateRequest) -> GuardianResponse:
        """보호자 등록"""
        guardian = await self.repo.create_guardian(
            user_id=user_id,
            name=data.name,
            phone_number=data.phone_number,
            email=data.email,
            relationship=data.relationship,
        )
        return GuardianResponse.model_validate(guardian)

    async def get_my_guardians(self, user_id: UUID) -> GuardianListResponse:
        """내 보호자 목록"""
        guardians = await self.repo.get_user_guardians(user_id)
        return GuardianListResponse(
            guardians=[GuardianResponse.model_validate(g) for g in guardians],
            total=len(guardians),
        )

    def calculate_expires_at(self, duration: ShareDuration) -> datetime:
        """기간 → 만료일 계산"""
        now = datetime.now()
        if duration == ShareDuration.ONE_DAY:
            return now + timedelta(days=1)
        elif duration == ShareDuration.ONE_WEEK:
            return now + timedelta(weeks=1)
        elif duration == ShareDuration.ONE_MONTH:
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=365)

    async def create_share_link(self, user_id: UUID, data: ShareLinkCreateRequest) -> ShareLinkResponse:
        """공유 링크 생성"""
        token = secrets.token_urlsafe(32)
        expires_at = self.calculate_expires_at(data.duration)

        share_link = await self.repo.create_share_link(
            user_id=user_id,
            guardian_id=data.guardian_id,
            token=token,
            duration=data.duration,
            categories=data.categories,
            include_summary_only=data.include_summary_only,
            expires_at=expires_at,
        )

        response = ShareLinkResponse.model_validate(share_link)
        response.guardian_id = data.guardian_id
        return response

    async def get_my_share_links(self, user_id: UUID) -> ShareLinkListResponse:
        """내 공유 링크 목록"""
        links = await self.repo.get_user_share_links(user_id)
        responses = []
        for link in links:
            r = ShareLinkResponse.model_validate(link)
            r.guardian_id = link.guardian_id
            responses.append(r)
        return ShareLinkListResponse(share_links=responses, total=len(responses))

    async def revoke_share_link(self, link_id: UUID) -> ShareLinkResponse:
        """공유 링크 철회"""
        link = await self.repo.revoke_share_link(link_id)
        response = ShareLinkResponse.model_validate(link)
        response.guardian_id = link.guardian_id
        return response
