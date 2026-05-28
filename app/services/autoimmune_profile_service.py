from __future__ import annotations

from datetime import datetime

from app.core import config
from app.dtos.autoimmune_profile import MedicationBulkCreateRequest, MedicationUpdateRequest, RiskProfileUpsertRequest
from app.models.user_medication import UserMedication
from app.models.user_risk_profile import UserRiskProfile
from app.models.users import User


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
