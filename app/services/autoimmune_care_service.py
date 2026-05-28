from __future__ import annotations

from urllib.parse import quote

from app.dtos.autoimmune_care import (
    MedicationCard,
    MedicationCardListResponse,
    PregnancySafetyResponse,
    SourceLink,
    VaccineInfoItem,
    VaccinePreventionResponse,
)
from app.models.user_risk_profile import PregnancyStatus
from app.models.users import User
from app.services.autoimmune_profile_service import MedicationService, RiskProfileService

# --- AUTO-003 ---
MFDS_DRUG_SEARCH_BASE = "https://nedrug.mfds.go.kr"

DISCONTINUATION_NOTICE = (
    "약을 임의로 중단하거나 용량을 바꾸면 질환이 악화될 수 있습니다. "
    "복용 변경이 필요하다고 느껴지면 반드시 담당 의료진과 먼저 상의하세요."
)

CONSULTATION_CHECKLIST = [
    "복용 중 불편하거나 평소와 달라진 점",
    "증상의 변화",
    "예정된 검사·접종 일정",
    "함께 복용 중인 다른 약이나 영양제",
]

REFERENCE_SOURCES = [
    SourceLink(name="식약처 의약품안전나라", url="https://nedrug.mfds.go.kr"),
    SourceLink(name="약학정보원", url="https://www.health.kr"),
    SourceLink(name="대한류마티스학회", url="https://www.rheum.or.kr"),
]

# --- AUTO-SAFE-001 ---
PREGNANCY_CONSULTATION_NOTICE = (
    "임신 중이거나 수유 중, 또는 임신을 계획하고 계신 경우 — 자가면역 질환 관리와 "
    "복용 중인 약물에 대해 담당 류마티스내과와 산부인과의 상담이 반드시 필요합니다."
)

PREGNANCY_GENERAL_INFO = [
    "임신·수유 시기의 자가면역 질환 관리는 류마티스내과와 산부인과의 협진이 권장됩니다.",
    "약물의 복용·중단에 대한 결정은 자가 판단하지 말고 담당 의료진과 상의하세요.",
    "임신 계획이 있다면 미리 담당 의료진에게 알리고 상담받는 것이 좋습니다.",
]

PREGNANCY_DISCLAIMER = (
    "약물별 임신·수유 중 안전성 판단은 담당 의료진의 영역입니다. 본 안내는 일반 정보이며 진료를 대체하지 않습니다."
)

# --- AUTO-PREV-001 ---
RECOMMENDED_VACCINES = [
    VaccineInfoItem(name="인플루엔자(독감)", description="면역억제 치료 중 환자에게 일반적으로 논의되는 백신입니다."),
    VaccineInfoItem(name="코로나19", description="면역억제 치료 중 환자에게 일반적으로 논의되는 백신입니다."),
    VaccineInfoItem(name="폐렴구균", description="면역억제 치료 중 환자에게 일반적으로 논의되는 백신입니다."),
    VaccineInfoItem(name="대상포진", description="면역억제 치료 중 환자에게 일반적으로 논의되는 백신입니다."),
]

LIVE_VACCINE_CAUTION = (
    "생백신은 면역억제제를 복용 중인 경우 접종이 권장되지 않을 수 있습니다. "
    "생백신 접종 여부는 반드시 담당 의료진과 상담하세요."
)

INFECTION_PREVENTION_TIPS = [
    "올바른 손 씻기를 생활화하세요.",
    "사람이 많은 곳에서는 마스크 착용을 고려하세요.",
    "감염병 유행 시기이거나 감염 노출이 의심될 때는 담당 의료진에게 알리세요.",
]

VACCINE_DISCLAIMER = (
    "접종 가능 여부와 접종 시기는 반드시 담당 의료진과 상담하세요. "
    "본 정보는 일반 안내이며 특정 백신을 권고하지 않습니다."
)

_APPLICABLE_STATUSES = {PregnancyStatus.PREGNANT, PregnancyStatus.BREASTFEEDING, PregnancyStatus.PLANNING}


def _build_mfds_search_url(drug_name: str) -> str:
    encoded = quote(drug_name)
    return f"{MFDS_DRUG_SEARCH_BASE}/searchDrug?itemName={encoded}"


class MedicationCardService:
    async def get_cards(self, user: User) -> MedicationCardListResponse:
        meds = await MedicationService().list_medications(user)
        cards = [
            MedicationCard(
                medication_id=med.id,
                name=med.name,
                drug_class=med.drug_class,
                is_injection=med.is_injection,
                user_note=med.note,
                discontinuation_notice=DISCONTINUATION_NOTICE,
                consultation_checklist=CONSULTATION_CHECKLIST,
                official_source_url=_build_mfds_search_url(med.name),
                reference_sources=REFERENCE_SOURCES,
            )
            for med in meds
        ]
        return MedicationCardListResponse(cards=cards)


class PregnancySafetyService:
    async def get_guidance(self, user: User) -> PregnancySafetyResponse:
        profile = await RiskProfileService().get_profile(user)
        status = profile.pregnancy_status if profile else PregnancyStatus.NONE
        applicable = status in _APPLICABLE_STATUSES
        if applicable:
            return PregnancySafetyResponse(
                applicable=True,
                pregnancy_status=status,
                consultation_notice=PREGNANCY_CONSULTATION_NOTICE,
                general_safety_info=PREGNANCY_GENERAL_INFO,
                disclaimer=PREGNANCY_DISCLAIMER,
            )
        return PregnancySafetyResponse(
            applicable=False,
            pregnancy_status=status,
            consultation_notice=None,
            general_safety_info=None,
            disclaimer=None,
        )


class VaccinePreventionService:
    def get_info(self) -> VaccinePreventionResponse:
        return VaccinePreventionResponse(
            recommended_vaccines=RECOMMENDED_VACCINES,
            live_vaccine_caution=LIVE_VACCINE_CAUTION,
            infection_prevention_tips=INFECTION_PREVENTION_TIPS,
            disclaimer=VACCINE_DISCLAIMER,
        )
