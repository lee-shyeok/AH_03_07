from tortoise.transactions import in_transaction
from app.dtos.users import UserModeUpdateRequest, UserUpdateRequest
from app.models.audit_logs import AuditAction, AuditLog
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.auth import AuthService
from app.core.utils.common import normalize_phone_number

class UserManageService:
    def __init__(self):
        self.repo = UserRepository()
        self.auth_service = AuthService()

    async def update_user(self, user: User, data: UserUpdateRequest) -> User:
        if data.email:
            await self.auth_service.check_email_exists(data.email)
        if data.phone_number:
            normalized_phone_number = normalize_phone_number(data.phone_number)
            await self.auth_service.check_phone_number_exists(normalized_phone_number)
            data.phone_number = normalized_phone_number
        async with in_transaction():
            await self.repo.update_instance(user=user, data=data.model_dump(exclude_none=True))
            await user.refresh_from_db()
        return user

    async def update_mode(self, user: User, data: UserModeUpdateRequest) -> User:
        """모드 전환 (REQ-MODE-002) - audit_logs에 기록"""
        before_mode = user.mode
        new_mode = data.mode

        if before_mode == new_mode:
            return user

        async with in_transaction():
            # 모드 업데이트
            user.mode = new_mode
            await user.save()

            # audit_logs 기록
            await AuditLog.create(
                user_id=user.id,
                action=AuditAction.MODE_CHANGE,
                before_value=before_mode.value,
                after_value=new_mode.value,
                note=f"사용자 모드 전환: {before_mode.value} → {new_mode.value}",
            )

        return user