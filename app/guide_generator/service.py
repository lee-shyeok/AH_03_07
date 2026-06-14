"""REQ-GUIDE-007 자가면역 안내문 출처 기반 생성 엔진 (Phase 2).

생성 트리거·입력 수집(REQ-AUTO-005)은 Phase 3 담당 — 이 모듈은 generate 엔진만.
"""

import json
import re

from openai import AsyncOpenAI

from app.core import config
from app.core.logger import default_logger as logger
from app.dtos.knowledge import KnowledgeChunk
from app.guide_generator.schema import GuideStatus, HealthGuideInput, HealthGuideOutput, SourceItem
from app.models.health_guide import HealthGuide
from app.services.knowledge_search import search_knowledge
from app.services.safety_filter import (
    SAFE_REPLACEMENTS,
    STANDARD_REPLACEMENT,
    apply_safety_filter,
    log_block_event,
)

_MODEL = "gpt-4o-mini"
_TEMPERATURE = 0.2

DEFAULT_DISCLAIMER = (
    "본 안내문은 일반 정보 제공 목적이며, 귀하의 상태에 대한 의학적 진단·처방·치료 권고가 아닙니다. "
    "의료적 결정은 반드시 담당 의료진과 상담하시기 바랍니다. (의료법 §27 준수)"
)
_DISCLAIMER = DEFAULT_DISCLAIMER

_BLOCKED_HIGH_RISK_MESSAGE = (
    "담당 의료진 검토가 필요한 항목이 확인되었습니다. 자동 안내문 생성이 보류됩니다. 담당 의료진과 상담하시기 바랍니다."
)

_GENERATION_FAILED_MESSAGE = "안내문 생성 중 오류가 발생했습니다. 담당 의료진과 상담하시기 바랍니다."

_SYSTEM_PROMPT = """당신은 자가면역 질환(루푸스, 류마티스관절염 등) 환자를 위한 의료 정보 안내문을 작성하는 어시스턴트입니다.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 일절 포함하지 마세요:
{
  "medication_general": "환자가 복용 중인 약물명을 명시하고 임상 자료에 근거한 일반 주의사항을 안내(용량·변경·중단·처방 표현 금지) (문자열)",
  "side_effect_monitoring": ["자가 관찰 포인트 1", "포인트 2"],
  "lifestyle_info": "생활습관 일반 정보 (문자열)",
  "symptom_summary": "다음 진료 시 참고할 증상 변화 (문자열)"
}

[생성 원칙]
- 반드시 제공된 임상 가이드라인 자료에만 근거하세요.
- 전문 의학 용어 대신 일상어를 사용하세요. 의학 약자(MTX·CBC·DMARD 등)는 풀어서 쓰세요.
- 한 문장은 30자 이내로 작성하세요.
- 활성도 점수·증상 강도는 직접 평가하지 마세요. "다음 진료 시 의료진과 공유하세요"로만 안내하세요.
- 약물 용량·변경·중단에 관한 표현을 절대 쓰지 마세요.
- 특정 약물의 병용이나 사용을 권장·추천하는 표현(예: '~와 함께 사용 권장')은 쓰지 마세요. 필요하면 '담당 의료진과 상의하세요'로 대체하세요.
- 진단·검사 결과 판독·치료 추천 표현을 절대 쓰지 마세요.
- 항상 담당 의료진과 상담하도록 안내하세요.
- 면책 조항은 작성하지 마세요 (시스템이 별도 첨부합니다).
"""

# JSON Schema (수동 검증 — 외부 라이브러리 불필요)
_REQUIRED_KEYS: set[str] = {"medication_general", "side_effect_monitoring", "lifestyle_info", "symptom_summary"}


def _build_rag_query(guide_input: HealthGuideInput) -> str:
    parts = list(dict.fromkeys(list(guide_input.disease_codes) + list(guide_input.medication_list)))
    if guide_input.medication_list:
        parts.append("복용 주의사항")
    return " ".join(parts) if parts else "자가면역 질환 치료 안내"


def _build_kb_context(chunks: list[KnowledgeChunk]) -> str:
    if not chunks:
        return "관련 임상 가이드라인 자료를 찾지 못했습니다."
    parts = []
    for i, c in enumerate(chunks, start=1):
        section = f" / {c.section_title}" if c.section_title else ""
        parts.append(
            f"[자료 {i}] {c.source_title}{section} "
            f"({c.source_organization}, {c.published_year}, p.{c.page_number})\n{c.text}"
        )
    return "\n\n".join(parts)


def _build_user_context(guide_input: HealthGuideInput) -> str:
    lines = [f"등록 질환: {', '.join(guide_input.disease_codes) or '미등록'}"]
    if guide_input.medication_list:
        lines.append(f"복용 약물: {', '.join(guide_input.medication_list)}")
        lines.append(
            "위 약물 각각에 대해 복용 시 일반적 주의사항을 임상 자료에 근거해 안내하세요 (용량·변경·중단 표현 금지)"
        )
    if guide_input.activity_score_summary:
        lines.append(f"활성도 요약(의료진 공유용): {guide_input.activity_score_summary}")
    if guide_input.risk_symptom_codes:
        lines.append(f"체크된 증상 코드: {', '.join(guide_input.risk_symptom_codes)}")
    if guide_input.lab_results_summary:
        lines.append(f"검사 요약(의료진 공유용): {guide_input.lab_results_summary}")
    if guide_input.pregnancy_lactation_codes:
        lines.append(f"임신·수유 상태: {', '.join(guide_input.pregnancy_lactation_codes)}")
    if guide_input.risk_factor_summary:
        lines.append(f"위험요인 요약(의료진 공유용): {guide_input.risk_factor_summary}")
    if guide_input.upcoming_appointments:
        lines.append(f"예정 진료·검사: {'; '.join(guide_input.upcoming_appointments)}")
    if guide_input.vaccine_infection_prevention:
        lines.append(f"백신·감염예방 정보: {guide_input.vaccine_infection_prevention}")
    return "\n".join(lines)


def _validate_llm_output(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM 출력이 JSON이 아닙니다: {exc}") from exc

    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"LLM 출력에 필수 필드 없음: {missing}")

    if not isinstance(data["medication_general"], str):
        raise ValueError("medication_general은 문자열이어야 합니다")
    if not isinstance(data["side_effect_monitoring"], list):
        raise ValueError("side_effect_monitoring은 목록이어야 합니다")
    if not isinstance(data["lifestyle_info"], str):
        raise ValueError("lifestyle_info는 문자열이어야 합니다")
    if not isinstance(data["symptom_summary"], str):
        raise ValueError("symptom_summary는 문자열이어야 합니다")

    return data


def _build_sources(chunks: list[KnowledgeChunk]) -> list[SourceItem]:
    seen: set[tuple] = set()
    sources: list[SourceItem] = []
    for c in chunks:
        key = (c.source_title, c.source_organization, c.published_year)
        if key not in seen:
            seen.add(key)
            sources.append(
                SourceItem(
                    title=c.source_title,
                    section=c.section_title,
                    page=c.page_number,
                    organization=c.source_organization,
                    published_year=c.published_year,
                    score=c.score,
                )
            )
    return sources


def _log_long_sentences(sections: dict, user_id: int) -> None:
    """[E] LLM 원문 기준 30자 초과 문장 soft 로깅 — 생성을 막지 않음."""
    over_count = 0
    for key, value in sections.items():
        texts: list[str] = value if key == "side_effect_monitoring" else [str(value)]
        for text in texts:
            for sentence in re.split(r"[.!?。]", text):
                if len(sentence.strip()) > 30:
                    over_count += 1
    if over_count:
        logger.info(
            json.dumps(
                {
                    "event": "guide_long_sentences",
                    "user_id": user_id,
                    "over_30_char_count": over_count,
                }
            )
        )


async def _apply_filters(sections: dict, user_id: int) -> dict:
    filtered: dict = {}
    for key, value in sections.items():
        replacement = SAFE_REPLACEMENTS.get(key, STANDARD_REPLACEMENT)
        if key == "side_effect_monitoring":
            result_list: list[str] = []
            for item in value:
                r = apply_safety_filter(str(item))
                if r.is_blocked:
                    await log_block_event(user_id, key, r.matched_patterns, str(item))
                    result_list.append(replacement)
                else:
                    result_list.append(item)
            filtered[key] = result_list
        else:
            r = apply_safety_filter(str(value))
            if r.is_blocked:
                await log_block_event(user_id, key, r.matched_patterns, str(value))
                filtered[key] = replacement
            else:
                filtered[key] = value
    return filtered


async def generate_guide(guide_input: HealthGuideInput) -> HealthGuideOutput:
    """8단계 안내문 생성 엔진."""

    # 고위험 플래그 우선 처리 — LLM·RAG 호출 없이 즉시 차단
    if guide_input.high_risk_flag:
        logger.info(
            json.dumps(
                {
                    "event": "guide_blocked_high_risk",
                    "user_id": guide_input.user_id,
                }
            )
        )
        guide = await HealthGuide.create(
            user_id=guide_input.user_id,
            status=GuideStatus.BLOCKED_HIGH_RISK.value,
            medication_general=_BLOCKED_HIGH_RISK_MESSAGE,
            side_effect_monitoring=[],
            lifestyle_info="",
            symptom_summary="",
            sources=[],
            disclaimer=_DISCLAIMER,
        )
        return HealthGuideOutput(
            user_id=guide_input.user_id,
            status=GuideStatus.BLOCKED_HIGH_RISK,
            medication_general=_BLOCKED_HIGH_RISK_MESSAGE,
            side_effect_monitoring=[],
            lifestyle_info="",
            symptom_summary="",
            sources=[],
            disclaimer=_DISCLAIMER,
            created_at=guide.created_at,
        )

    # Step 2: 지식베이스 유사도 검색 (REQ-KB-002 재사용)
    query = _build_rag_query(guide_input)
    chunks = await search_knowledge(query, top_k=5)

    # Step 3: 컨텍스트 구성
    user_content = (
        f"[임상 가이드라인 자료]\n{_build_kb_context(chunks)}\n\n[환자 정보]\n{_build_user_context(guide_input)}"
    )

    # Step 4: LLM 안내문 생성 (Temperature 0.2, JSON 출력 강제)
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    completion = await client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=_TEMPERATURE,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    raw_llm_output = completion.choices[0].message.content or ""

    # Step 5: JSON Schema 검증 — 실패 시 크래시하지 않고 안전 폴백 반환
    try:
        sections = _validate_llm_output(raw_llm_output)
    except ValueError as exc:
        logger.error(
            json.dumps(
                {
                    "event": "guide_llm_validation_error",
                    "user_id": guide_input.user_id,
                    "error": str(exc),
                }
            )
        )
        guide = await HealthGuide.create(
            user_id=guide_input.user_id,
            status=GuideStatus.GENERATION_FAILED.value,
            medication_general=_GENERATION_FAILED_MESSAGE,
            side_effect_monitoring=[],
            lifestyle_info="",
            symptom_summary="",
            sources=[],
            disclaimer=_DISCLAIMER,
        )
        return HealthGuideOutput(
            user_id=guide_input.user_id,
            status=GuideStatus.GENERATION_FAILED,
            medication_general=_GENERATION_FAILED_MESSAGE,
            side_effect_monitoring=[],
            lifestyle_info="",
            symptom_summary="",
            sources=[],
            disclaimer=_DISCLAIMER,
            created_at=guide.created_at,
        )

    # [E] 30자 초과 문장 soft 로깅 — LLM 원문 기준, 생성 차단 없음
    _log_long_sentences(sections, guide_input.user_id)

    # Step 6: 출처 메타데이터 첨부 (REQ-KB-003 재사용)
    sources = _build_sources(chunks)

    # Step 7: NFR-SAFE-003 다단계 필터 적용
    filtered = await _apply_filters(sections, guide_input.user_id)

    # Step 8: HealthGuide 저장
    guide = await HealthGuide.create(
        user_id=guide_input.user_id,
        status=GuideStatus.GENERATED.value,
        medication_general=filtered["medication_general"],
        side_effect_monitoring=filtered["side_effect_monitoring"],
        lifestyle_info=filtered["lifestyle_info"],
        symptom_summary=filtered["symptom_summary"],
        sources=[s.model_dump() for s in sources],
        disclaimer=_DISCLAIMER,
    )

    logger.info(
        json.dumps(
            {
                "event": "guide_generated",
                "user_id": guide_input.user_id,
                "chunk_count": len(chunks),
                "source_count": len(sources),
            }
        )
    )

    return HealthGuideOutput(
        user_id=guide_input.user_id,
        status=GuideStatus.GENERATED,
        medication_general=filtered["medication_general"],
        side_effect_monitoring=filtered["side_effect_monitoring"],
        lifestyle_info=filtered["lifestyle_info"],
        symptom_summary=filtered["symptom_summary"],
        sources=sources,
        disclaimer=_DISCLAIMER,
        created_at=guide.created_at,
    )
