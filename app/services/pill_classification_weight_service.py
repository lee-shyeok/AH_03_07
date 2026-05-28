from __future__ import annotations

from pydantic import BaseModel

from app.models.user_disease import DiseaseCode, UserDisease
from app.models.user_medication import DrugClass
from app.models.users import User

AUTOIMMUNE_DRUG_NAME_TO_CLASS: dict[str, DrugClass] = {
    "메토트렉세이트": DrugClass.IMMUNOSUPPRESSANT,
    "하이드록시클로로퀸": DrugClass.ANTIMALARIAL,
    "설파살라진": DrugClass.IMMUNOSUPPRESSANT,
    "인플릭시맙": DrugClass.BIOLOGIC,
    "아달리무맙": DrugClass.BIOLOGIC,
    "프레드니솔론": DrugClass.STEROID,
}

DISEASE_TO_DRUG_CLASSES: dict[DiseaseCode, set[DrugClass]] = {
    DiseaseCode.RA: {
        DrugClass.STEROID,
        DrugClass.IMMUNOSUPPRESSANT,
        DrugClass.ANTIMALARIAL,
        DrugClass.BIOLOGIC,
    },
    DiseaseCode.SLE: {
        DrugClass.STEROID,
        DrugClass.IMMUNOSUPPRESSANT,
        DrugClass.ANTIMALARIAL,
    },
}

AUTOIMMUNE_BOOST_MULTIPLIER = 1.3


class PillCandidate(BaseModel):
    drug_name: str
    confidence: float  # 원본, 불변 — status 판정 기준
    adjusted_score: float = 0.0  # 가중치 적용 정렬용 (confidence 와 분리)
    autoimmune_match: bool = False


class PillClassificationWeightService:
    async def apply_autoimmune_weights(self, user: User, candidates: list[PillCandidate]) -> list[PillCandidate]:
        relevant = await self._get_relevant_drug_classes(user)

        for c in candidates:
            c.adjusted_score = c.confidence  # 기본값: 원본 신뢰도
            if not relevant:
                continue
            drug_class = AUTOIMMUNE_DRUG_NAME_TO_CLASS.get(c.drug_name)
            if drug_class in relevant:
                c.adjusted_score = c.confidence * AUTOIMMUNE_BOOST_MULTIPLIER
                c.autoimmune_match = True

        # 재정렬 보류 — "추천" 행위 금지 제약(NFR-SAFE-003) 및 멘토 확인 전
        return candidates

    async def _get_relevant_drug_classes(self, user: User) -> set[DrugClass]:
        codes = await UserDisease.filter(user=user, deleted_at=None).values_list("disease_code", flat=True)
        relevant: set[DrugClass] = set()
        for code in codes:
            relevant.update(DISEASE_TO_DRUG_CLASSES.get(code, set()))
        return relevant


# ─── 통합 어댑터 가이드 (권순현님 작업 머지 후 적용) ────────────────────────
#
# 권순현님 PillRecognitionResponse 구조 (예상):
#   top1_drug_name: str, top1_confidence: float
#   top2_drug_name: str, top2_confidence: float
#   top3_drug_name: str, top3_confidence: float
#   status: str  # "COMPLETED" | "LOW_CONFIDENCE"  (0.7 임계값 기준)
#
# 통합 시 변환 패턴:
#   candidates = [
#       PillCandidate(drug_name=resp.top1_drug_name, confidence=resp.top1_confidence),
#       PillCandidate(drug_name=resp.top2_drug_name, confidence=resp.top2_confidence),
#       PillCandidate(drug_name=resp.top3_drug_name, confidence=resp.top3_confidence),
#   ]
#   weighted = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
#
# ⚠ status 판정은 권순현님 원본 confidence 기준 그대로 유지.
#   weighted[i].confidence 는 절대 변경되지 않으므로 status 재판정 불필요.
