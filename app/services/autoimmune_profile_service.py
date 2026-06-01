from __future__ import annotations

from datetime import datetime

from app.core import config
from app.dtos.autoimmune_profile import (
    AutoimmuneProfileUpsertRequest,
    MedicationBulkCreateRequest,
    MedicationUpdateRequest,
    RiskProfileUpsertRequest,
)
from app.models.autoimmune_profile import AutoimmunePregnancyStatus, AutoimmuneProfile
from app.models.user_medication import UserMedication
from app.models.user_risk_profile import UserRiskProfile
from app.models.users import User

_PREGNANCY_ADVISORY = "담당 류마티스내과 및 산부인과 상담이 필요합니다."
_ADVISORY_STATUSES = {
    AutoimmunePregnancyStatus.PREGNANT,
    AutoimmunePregnancyStatus.BREASTFEEDING,
    AutoimmunePregnancyStatus.PLANNING,
}


class AutoimmuneProfileService:
    async def get_profile(self, user: User) -> AutoimmuneProfile | None:
        return await AutoimmuneProfile.get_or_none(user=user)

    async def upsert_profile(self, user: User, data: AutoimmuneProfileUpsertRequest) -> AutoimmuneProfile:
        profile = await AutoimmuneProfile.get_or_none(user=user)
        if profile is None:
            return await AutoimmuneProfile.create(
                user=user,
                risk_factors=data.risk_factors,
                pregnancy_status=data.pregnancy_status,
                vaccination_history=data.vaccination_history,
            )
        profile.risk_factors = data.risk_factors
        profile.pregnancy_status = data.pregnancy_status
        profile.vaccination_history = data.vaccination_history
        await profile.save(update_fields=["risk_factors", "pregnancy_status", "vaccination_history", "updated_at"])
        return profile

    @staticmethod
    def advisory_message(profile: AutoimmuneProfile) -> str | None:
        if profile.pregnancy_status in _ADVISORY_STATUSES:
            return _PREGNANCY_ADVISORY
        return None


class RiskProfileService:
    async def upsert_profile(self, user: User, data: RiskProfileUpsertRequest) -> UserRiskProfile:
        profile = await UserRiskProfile.get_or_none(user=user)
        if profile is None:
            return await UserRiskProfile.create(
                user=user,
                pregnancy_status=data.pregnancy_status,
                renal_impairment=data.renal_impairment,
                hepatic_impairment=data.hepatic_impairment,
                infection_history=data.infection_history,
                drug_allergy=data.drug_allergy,
                comorbidities=data.comorbidities,
            )
        update_data = data.model_dump()
        update_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(profile, field, value)
        profile.updated_at = datetime.now(config.TIMEZONE)
        update_fields.append("updated_at")
        await profile.save(update_fields=update_fields)
        return profile

    async def get_profile(self, user: User) -> UserRiskProfile | None:
        return await UserRiskProfile.get_or_none(user=user)


class MedicationService:
    async def create_medications(self, user: User, data: MedicationBulkCreateRequest) -> list[UserMedication]:
        medications = []
        for item in data.medications:
            med = await UserMedication.create(
                user=user,
                name=item.name,
                drug_class=item.drug_class,
                is_injection=item.is_injection,
                note=item.note,
            )
            medications.append(med)
        return medications

    async def list_medications(self, user: User) -> list[UserMedication]:
        return await UserMedication.filter(user=user, deleted_at=None).order_by("created_at")

    async def update_medication(
        self, user: User, medication_id: int, data: MedicationUpdateRequest
    ) -> UserMedication | None:
        med = await UserMedication.get_or_none(id=medication_id, user=user, deleted_at=None)
        if med is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        update_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(med, field, value)
        if update_fields:
            med.updated_at = datetime.now(config.TIMEZONE)
            update_fields.append("updated_at")
            await med.save(update_fields=update_fields)
        return med

    async def delete_medication(self, user: User, medication_id: int) -> bool:
        med = await UserMedication.get_or_none(id=medication_id, user=user, deleted_at=None)
        if med is None:
            return False
        med.deleted_at = datetime.now(config.TIMEZONE)
        await med.save(update_fields=["deleted_at"])
        return True
