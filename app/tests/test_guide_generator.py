import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.dtos.knowledge import KnowledgeChunk
from app.guide_generator.schema import GuideStatus, HealthGuideInput
from app.guide_generator.service import _DISCLAIMER, generate_guide
from app.services.safety_filter import apply_safety_filter

# ── 공통 픽스처 ──────────────────────────────────────────────

_VALID_LLM_JSON = json.dumps(
    {
        "medication_general": "약물 복용 시 의료진 지시를 따르세요.",
        "side_effect_monitoring": ["두통이 생기면 의료진에게 알려주세요.", "구토 증상 시 상담하세요."],
        "lifestyle_info": "규칙적인 생활을 유지하세요.",
        "symptom_summary": "증상 변화를 다음 진료 시 의료진과 공유하세요.",
    }
)

_FAKE_CHUNK = KnowledgeChunk(
    document_id=1,
    chunk_index=0,
    text="EULAR 류마티스관절염 치료 지침 내용",
    score=0.88,
    page_number=5,
    section_title="약물 치료",
    source_title="EULAR 2022",
    source_organization="EULAR",
    published_year=2022,
)

_FAKE_CREATED_AT = datetime(2026, 5, 27, 0, 0, 0, tzinfo=UTC)


def _make_input(**kwargs) -> HealthGuideInput:
    defaults = dict(user_id=1, disease_codes=["RA"], high_risk_flag=False)
    defaults.update(kwargs)
    return HealthGuideInput(**defaults)


def _mock_completion(content: str) -> MagicMock:
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = content
    return completion


def _mock_health_guide_create() -> AsyncMock:
    mock_guide = MagicMock()
    mock_guide.created_at = _FAKE_CREATED_AT
    return AsyncMock(return_value=mock_guide)


# ── 고위험 플래그 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_high_risk_flag_blocks_llm():
    """고위험 플래그 True → LLM 미호출, 단일 차단 문구 반환."""
    with (
        patch("app.guide_generator.service.search_knowledge") as mock_search,
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai,
        patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
    ):
        result = await generate_guide(_make_input(high_risk_flag=True))

    mock_search.assert_not_called()
    mock_openai.assert_not_called()
    assert result.status == GuideStatus.BLOCKED_HIGH_RISK
    assert "담당 의료진" in result.medication_general
    assert result.side_effect_monitoring == []
    assert result.disclaimer == _DISCLAIMER


# ── JSON Schema 검증 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_valid_llm_json_generates_guide():
    """유효한 JSON → GENERATED 상태로 반환."""
    with (
        patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[_FAKE_CHUNK])),
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
        patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
    ):
        mock_openai_cls.return_value.chat.completions.create = AsyncMock(return_value=_mock_completion(_VALID_LLM_JSON))
        result = await generate_guide(_make_input())

    assert result.status == GuideStatus.GENERATED
    assert result.medication_general != ""
    assert isinstance(result.side_effect_monitoring, list)
    assert result.disclaimer == _DISCLAIMER


@pytest.mark.asyncio
async def test_invalid_json_from_llm_returns_fallback():
    """JSON이 아닌 LLM 응답 → 크래시 없이 GENERATION_FAILED 폴백 반환."""
    with (
        patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[])),
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
        patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
    ):
        mock_openai_cls.return_value.chat.completions.create = AsyncMock(
            return_value=_mock_completion("이것은 JSON이 아닙니다")
        )
        result = await generate_guide(_make_input())

    assert result.status == GuideStatus.GENERATION_FAILED
    assert "담당 의료진" in result.medication_general
    assert result.disclaimer == _DISCLAIMER


@pytest.mark.asyncio
async def test_missing_required_key_returns_fallback():
    """필수 키 누락 JSON → 크래시 없이 GENERATION_FAILED 폴백 반환."""
    incomplete = json.dumps({"medication_general": "안내", "lifestyle_info": "정보"})
    with (
        patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[])),
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
        patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
    ):
        mock_openai_cls.return_value.chat.completions.create = AsyncMock(return_value=_mock_completion(incomplete))
        result = await generate_guide(_make_input())

    assert result.status == GuideStatus.GENERATION_FAILED


# ── NFR-SAFE-003 필터 ─────────────────────────────────────────


def test_safety_filter_blocks_drug_stop_expression():
    """'중단하세요' 포함 텍스트 → 차단, 정형 문구 대체."""
    result = apply_safety_filter("메토트렉세이트 복용을 중단하세요.")
    assert result.is_blocked is True
    assert result.filtered_text == "담당 의료진과 상담하시기 바랍니다."


def test_safety_filter_blocks_synonym_drug_stop():
    """동의어 '끊으세요' → 차단."""
    result = apply_safety_filter("약을 끊으세요.")
    assert result.is_blocked is True


def test_safety_filter_allows_safe_expression():
    """안전 표현만 있는 문장 → 통과."""
    result = apply_safety_filter("이상 증상이 있으면 담당 의료진과 상담하시기 바랍니다.")
    assert result.is_blocked is False


def test_safety_filter_blocks_when_forbidden_and_safe_coexist():
    """금지 표현과 안전 표현이 같은 텍스트에 있을 때 → 금지 표현 우선 차단.

    시스템 프롬프트가 LLM에 '담당 의료진과 상담' 안내를 강제하므로
    거의 모든 응답에 안전 표현이 포함된다.
    화이트리스트 전역 우회가 없어야 이 케이스가 정상 차단된다.
    """
    text = "약을 중단하세요. 담당 의료진과 상담하시기 바랍니다."
    result = apply_safety_filter(text)
    assert result.is_blocked is True
    assert result.filtered_text == "담당 의료진과 상담하시기 바랍니다."


def test_safety_filter_blocks_drug_adjust_with_safe_expression():
    """용량 조절 표현 + 안전 표현 혼재 → 차단."""
    text = "용량 조절이 필요합니다. 담당 의료진과 상담하세요."
    result = apply_safety_filter(text)
    assert result.is_blocked is True


@pytest.mark.asyncio
async def test_forbidden_expression_in_llm_output_is_replaced():
    """LLM이 금지 표현 생성 → 해당 섹션 정형 문구로 대체."""
    bad_json = json.dumps(
        {
            "medication_general": "메토트렉세이트 복용을 중단하세요.",
            "side_effect_monitoring": ["구토 시 의료진에게 알려주세요."],
            "lifestyle_info": "규칙적인 생활을 하세요.",
            "symptom_summary": "증상 변화를 기록하세요.",
        }
    )
    with (
        patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[])),
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
        patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
    ):
        mock_openai_cls.return_value.chat.completions.create = AsyncMock(return_value=_mock_completion(bad_json))
        result = await generate_guide(_make_input())

    assert result.medication_general == "담당 의료진과 상담하시기 바랍니다."
    assert result.status == GuideStatus.GENERATED


# ── 출처 메타데이터·면책 조항 ──────────────────────────────────


@pytest.mark.asyncio
async def test_sources_attached_from_rag_metadata():
    """RAG 청크 메타데이터 → sources 필드에 첨부."""
    with (
        patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[_FAKE_CHUNK])),
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
        patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
    ):
        mock_openai_cls.return_value.chat.completions.create = AsyncMock(return_value=_mock_completion(_VALID_LLM_JSON))
        result = await generate_guide(_make_input())

    assert len(result.sources) == 1
    assert result.sources[0].title == "EULAR 2022"
    assert result.sources[0].organization == "EULAR"
    assert result.sources[0].published_year == 2022


@pytest.mark.asyncio
async def test_disclaimer_always_present():
    """모든 안내문에 면책 조항 강제 포함."""
    for flag in [False, True]:
        with (
            patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[])),
            patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
            patch("app.guide_generator.service.HealthGuide.create", _mock_health_guide_create()),
        ):
            mock_openai_cls.return_value.chat.completions.create = AsyncMock(
                return_value=_mock_completion(_VALID_LLM_JSON)
            )
            result = await generate_guide(_make_input(high_risk_flag=flag))
        assert _DISCLAIMER in result.disclaimer, f"high_risk_flag={flag}: disclaimer 없음"


# ── HealthGuide 저장 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_guide_create_called_once():
    """generate_guide 성공 시 HealthGuide.create 1회 호출."""
    mock_create = _mock_health_guide_create()
    with (
        patch("app.guide_generator.service.search_knowledge", AsyncMock(return_value=[_FAKE_CHUNK])),
        patch("app.guide_generator.service.AsyncOpenAI") as mock_openai_cls,
        patch("app.guide_generator.service.HealthGuide.create", mock_create),
    ):
        mock_openai_cls.return_value.chat.completions.create = AsyncMock(return_value=_mock_completion(_VALID_LLM_JSON))
        await generate_guide(_make_input())

    mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_guide_create_called_on_high_risk():
    """고위험 차단 시에도 HealthGuide.create 1회 호출 (BLOCKED 상태로 저장)."""
    mock_create = _mock_health_guide_create()
    with (
        patch("app.guide_generator.service.search_knowledge"),
        patch("app.guide_generator.service.AsyncOpenAI"),
        patch("app.guide_generator.service.HealthGuide.create", mock_create),
    ):
        await generate_guide(_make_input(high_risk_flag=True))

    mock_create.assert_awaited_once()
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["status"] == GuideStatus.BLOCKED_HIGH_RISK.value
