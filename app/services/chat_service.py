import json

from openai import AsyncOpenAI, OpenAIError

from app.core import config
from app.core.logger import default_logger as logger
from app.dtos.knowledge import KnowledgeChunk
from app.services.knowledge_search import search_knowledge

_MODEL = "gpt-4o-mini"
RAG_SCORE_THRESHOLD = 0.47  # 이 값 미만 청크는 무관한 결과로 간주

_SYSTEM_PROMPT = """당신은 자가면역 질환(루푸스, 류마티스관절염 등) 환자를 돕는 의료 정보 안내 어시스턴트입니다.

[답변 원칙]
- 반드시 아래 제공된 임상 가이드라인 자료에 근거해서만 답변하세요.
- 자료에 없는 내용은 "제공된 자료에서 확인되지 않습니다"라고 명확히 말하세요.
- 의료 진단, 처방, 약물 용량 조절은 절대 하지 마세요.
- 진단·처방·검사 판독 등 의료적 판단이 필요한 질문에는 반드시 "담당 의료진 상담을 권고합니다"라고 안내하세요.
- 약물의 용량·복용법·복용 빈도는 지식베이스에 자료가 있더라도 구체적으로 안내하지 말고, 항상 담당 의료진과 상담하도록 안내할 것.
- 건강·의료와 무관한 질문(예: 날씨, 일반 상식)에는 의료 안내 전용 챗봇임을 밝히고 정중히 거절할 것.
- 한국어로, 환자가 이해하기 쉬운 표현으로 답변하세요.
- 답변 마지막에 반드시 다음 면책 문구를 포함하세요:
  "※ 이 안내는 의료 진단이나 처방을 대체하지 않습니다. 증상이 있으면 반드시 담당 의료진과 상담하세요."
"""


def _build_context(chunks: list[KnowledgeChunk]) -> str:
    """검색된 청크를 LLM 프롬프트용 컨텍스트 문자열로 조립한다.

    나중에 사용자 질환·활성도 로그를 추가할 때 이 함수를 확장하면 된다.
    """
    if not chunks:
        return "관련 임상 가이드라인 자료를 찾지 못했습니다."

    parts = []
    for i, chunk in enumerate(chunks, start=1):
        section = f" / {chunk.section_title}" if chunk.section_title else ""
        parts.append(
            f"[자료 {i}] {chunk.source_title}{section} "
            f"({chunk.source_organization}, {chunk.published_year}, p.{chunk.page_number})\n"
            f"{chunk.text}"
        )
    return "\n\n".join(parts)


async def chat_with_rag(message: str) -> dict:
    """RAG 검색 → GPT-4o-mini 호출 → 응답 딕셔너리 반환.

    반환 형태: {"answer": str, "is_general_info": bool, "sources": list[dict]}
    """
    try:
        chunks = await search_knowledge(message, top_k=5)
    except Exception as exc:
        logger.error(json.dumps({"event": "chat_search_error", "error": str(exc)}))
        raise RuntimeError(f"지식베이스 검색 실패: {exc}") from exc

    # 임계값 미만 청크 제거 — 이 리스트 하나가 LLM 컨텍스트와 sources를 모두 결정
    relevant_chunks = [c for c in chunks if c.score >= RAG_SCORE_THRESHOLD]
    is_general_info = len(relevant_chunks) == 0

    context = _build_context(relevant_chunks)
    user_content = f"[임상 가이드라인 자료]\n{context}\n\n[환자 질문]\n{message}"

    try:
        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        answer = completion.choices[0].message.content or ""
    except OpenAIError as exc:
        logger.error(json.dumps({"event": "chat_llm_error", "error": str(exc)}))
        raise RuntimeError(f"LLM 호출 실패: {exc}") from exc

    sources = [
        {
            "title": c.source_title,
            "section": c.section_title,
            "page": c.page_number,
            "organization": c.source_organization,
            "published_year": c.published_year,
            "score": c.score,
        }
        for c in relevant_chunks
    ]

    logger.info(
        json.dumps(
            {
                "event": "chat_response",
                "chunk_count": len(relevant_chunks),
                "is_general_info": is_general_info,
            }
        )
    )

    return {"answer": answer, "is_general_info": is_general_info, "sources": sources}
