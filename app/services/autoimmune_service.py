from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException

from app.core import config
from app.dtos.autoimmune import DiseaseBulkCreateRequest, DiseaseUpdateRequest
from app.models.audit_log import AuditLog
from app.models.user_consents import ConsentType
from app.models.user_disease import UserDisease
from app.models.users import User, UserMode
from app.services.user_consents import UserConsentService


class ModeService:
    async def update_mode(self, user: User, new_mode: UserMode) -> User:
        if new_mode == UserMode.AUTOIMMUNE:
            consent_service = UserConsentService()
            if not await consent_service.is_consent_active(user.id, ConsentType.MEDICAL_DATA):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "CONSENT_REQUIRED",
                        "message": "민감정보 처리 동의가 필요합니다.",
                        "details": {"consent_types": ["medical_data"]},
                    },
                )
        if user.mode != new_mode:
            await AuditLog.create(
                user=user,
                action="MODE_SWITCH",
                detail={"from": str(user.mode), "to": str(new_mode)},
            )
            user.mode = new_mode
            user.mode_selected_at = datetime.now(config.TIMEZONE)
            user.updated_at = datetime.now(config.TIMEZONE)
            await user.save(update_fields=["mode", "mode_selected_at", "updated_at"])
        return user


class DiseaseService:
    async def create_diseases(self, user: User, data: DiseaseBulkCreateRequest) -> list[UserDisease]:
        diseases = []
        for item in data.diseases:
            d = await UserDisease.create(
                user=user,
                disease_code=item.disease_code,
                diagnosed_date=item.diagnosed_date,
                note=item.note,
            )
            diseases.append(d)
        return diseases

    async def list_diseases(self, user: User) -> list[UserDisease]:
        return await UserDisease.filter(user=user, deleted_at=None).order_by("created_at")

    async def update_disease(self, user: User, disease_id: int, data: DiseaseUpdateRequest) -> UserDisease | None:
        disease = await UserDisease.get_or_none(id=disease_id, user=user, deleted_at=None)
        if disease is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        update_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(disease, field, value)
        if update_fields:
            disease.updated_at = datetime.now(config.TIMEZONE)
            update_fields.append("updated_at")
            await disease.save(update_fields=update_fields)
        return disease

    async def delete_disease(self, user: User, disease_id: int) -> bool:
        disease = await UserDisease.get_or_none(id=disease_id, user=user, deleted_at=None)
        if disease is None:
            return False
        disease.deleted_at = datetime.now(config.TIMEZONE)
        await disease.save(update_fields=["deleted_at"])
        return True
