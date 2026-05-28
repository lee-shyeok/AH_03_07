from __future__ import annotations

from datetime import date

from tortoise.contrib.test import TestCase

from app.models.user_disease import DiseaseCode, UserDisease
from app.models.users import Gender, User
from app.services.pill_classification_weight_service import (
    AUTOIMMUNE_BOOST_MULTIPLIER,
    PillCandidate,
    PillClassificationWeightService,
)


async def _create_user(suffix: str) -> User:
    return await User.create(
        email=f"pill_weight_{suffix}@example.com",
        hashed_password="hashed",
        name=f"테스터{suffix}",
        gender=Gender.FEMALE,
        birthday=date(1990, 1, 1),
        phone_number=f"0100000{suffix}",
    )


async def _register_disease(user: User, code: DiseaseCode) -> None:
    await UserDisease.create(user=user, disease_code=code)


class TestPillClassificationWeightService(TestCase):
    # ── 1. 질환 미등록 → 전 후보 adjusted_score=confidence, match=False ──

    async def test_no_disease_no_boost(self):
        user = await _create_user("001")
        candidates = [
            PillCandidate(drug_name="메토트렉세이트", confidence=0.9),
            PillCandidate(drug_name="프레드니솔론", confidence=0.8),
        ]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        for c in result:
            assert c.adjusted_score == c.confidence
            assert c.autoimmune_match is False

    # ── 2. RA + 메토트렉세이트 → adjusted_score = conf × 1.3, match=True ──

    async def test_ra_immunosuppressant_boosted(self):
        user = await _create_user("002")
        await _register_disease(user, DiseaseCode.RA)
        conf = 0.85
        candidates = [PillCandidate(drug_name="메토트렉세이트", confidence=conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        assert result[0].adjusted_score == pytest_approx(conf * AUTOIMMUNE_BOOST_MULTIPLIER)
        assert result[0].autoimmune_match is True

    # ── 3. RA + 하이드록시클로로퀸 → 가중치 적용 ──

    async def test_ra_antimalarial_boosted(self):
        user = await _create_user("003")
        await _register_disease(user, DiseaseCode.RA)
        conf = 0.75
        candidates = [PillCandidate(drug_name="하이드록시클로로퀸", confidence=conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        assert result[0].adjusted_score == pytest_approx(conf * AUTOIMMUNE_BOOST_MULTIPLIER)
        assert result[0].autoimmune_match is True

    # ── 4. RA + 아달리무맙(생물학적 제제) → 가중치 적용 ──

    async def test_ra_biologic_boosted(self):
        user = await _create_user("004")
        await _register_disease(user, DiseaseCode.RA)
        conf = 0.65
        candidates = [PillCandidate(drug_name="아달리무맙", confidence=conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        assert result[0].adjusted_score == pytest_approx(conf * AUTOIMMUNE_BOOST_MULTIPLIER)
        assert result[0].autoimmune_match is True

    # ── 5. SLE + 프레드니솔론(스테로이드) → 가중치 적용 ──

    async def test_sle_steroid_boosted(self):
        user = await _create_user("005")
        await _register_disease(user, DiseaseCode.SLE)
        conf = 0.80
        candidates = [PillCandidate(drug_name="프레드니솔론", confidence=conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        assert result[0].adjusted_score == pytest_approx(conf * AUTOIMMUNE_BOOST_MULTIPLIER)
        assert result[0].autoimmune_match is True

    # ── 6. 룩업 맵에 없는 약품명 → 변경 없음 ──

    async def test_unknown_drug_name_not_boosted(self):
        user = await _create_user("006")
        await _register_disease(user, DiseaseCode.RA)
        conf = 0.90
        candidates = [PillCandidate(drug_name="타이레놀", confidence=conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        assert result[0].adjusted_score == conf
        assert result[0].autoimmune_match is False

    # ── 7. 등록 질환과 무관한 약물군 → 변경 없음 ──
    # SLE 등록 사용자에게 RA 전용이 아닌 BIOLOGIC(SLE 약물군 미포함) → 미적용

    async def test_non_relevant_class_not_boosted(self):
        user = await _create_user("007")
        await _register_disease(user, DiseaseCode.SLE)
        conf = 0.88
        # 아달리무맙 = BIOLOGIC, SLE 약물군에 BIOLOGIC 미포함
        candidates = [PillCandidate(drug_name="아달리무맙", confidence=conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        assert result[0].adjusted_score == conf
        assert result[0].autoimmune_match is False

    # ── 8. RA + SLE 둘 다 등록 → union 약물군 모두 대상 ──

    async def test_multiple_diseases_union(self):
        user = await _create_user("008")
        await _register_disease(user, DiseaseCode.RA)
        await _register_disease(user, DiseaseCode.SLE)
        conf_ra = 0.70
        conf_sle = 0.72
        # 아달리무맙(BIOLOGIC) = RA만 포함, 프레드니솔론(STEROID) = RA+SLE 공통
        candidates = [
            PillCandidate(drug_name="아달리무맙", confidence=conf_ra),
            PillCandidate(drug_name="프레드니솔론", confidence=conf_sle),
        ]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        # RA+SLE union → BIOLOGIC 포함되므로 아달리무맙도 부스트
        assert result[0].adjusted_score == pytest_approx(conf_ra * AUTOIMMUNE_BOOST_MULTIPLIER)
        assert result[0].autoimmune_match is True
        assert result[1].adjusted_score == pytest_approx(conf_sle * AUTOIMMUNE_BOOST_MULTIPLIER)
        assert result[1].autoimmune_match is True

    # ── 9. ★핵심 안전 테스트★ 가중치 후에도 confidence 원본 불변 ──

    async def test_confidence_unchanged_after_boost(self):
        user = await _create_user("009")
        await _register_disease(user, DiseaseCode.RA)
        original_conf = 0.60
        candidates = [PillCandidate(drug_name="메토트렉세이트", confidence=original_conf)]
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, candidates)
        # adjusted_score는 부스트되어야 하지만
        assert result[0].adjusted_score == pytest_approx(original_conf * AUTOIMMUNE_BOOST_MULTIPLIER)
        # confidence는 절대 변경되지 않음 (status 판정 기준 보호)
        assert result[0].confidence == original_conf

    # ── 10. 빈 리스트 입력 → 빈 리스트 반환 ──

    async def test_empty_candidates(self):
        user = await _create_user("010")
        await _register_disease(user, DiseaseCode.RA)
        result = await PillClassificationWeightService().apply_autoimmune_weights(user, [])
        assert result == []


def pytest_approx(value: float) -> float:
    """float 부동소수점 비교 헬퍼 (pytest.approx 래퍼)."""
    import pytest

    return pytest.approx(value, rel=1e-6)
