from __future__ import annotations

from openai import AsyncOpenAI

from app.core import config
from app.dtos.knowledge import KnowledgeChunk
from app.services.knowledge_search import search_knowledge

LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 1024
RAG_SCORE_THRESHOLD = 0.47

SAFETY_SYSTEM_PROMPT = """당신은 자가면역 질환자를 위한 의료 정보 안내 어시스턴트입니다.
- 제공된 참고 자료에만 근거하여 답하세요.
- 관련 자료가 없으면 그렇게 명시하세요.
- 진단·처방 등 의학적 판단은 절대 하지 마세요.
- 의학적 결정이 필요한 경우 의료진과의 상담을 권유하세요.
- 한국어로 응답하세요."""


class ChatRAGService:
    def filter_by_threshold(
        self, chunks: list[KnowledgeChunk], threshold: float = RAG_SCORE_THRESHOLD
    ) -> list[KnowledgeChunk]:
        return [c for c in chunks if c.score >= threshold]

    def build_context(self, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return ""
        return "\n\n".join(f"[자료 {i + 1}] {c.text}" for i, c in enumerate(chunks))

    def to_sources(self, chunks: list[KnowledgeChunk]) -> list[dict]:
        results = []
        for c in chunks:
            title = c.source_title
            if c.source_organization:
                title = f"{title} — {c.source_organization}"
            snippet = c.text[:200] + "..." if len(c.text) > 200 else c.text
            results.append({"title": title, "url": None, "snippet": snippet})
        return results

    async def generate_response(self, user_message: str, top_k: int = 5) -> dict:
        chunks = await search_knowledge(user_message, top_k=top_k)
        relevant = self.filter_by_threshold(chunks)
        is_general_info = len(relevant) == 0
        context = self.build_context(relevant)

        user_content = (
            f"질문: {user_message}\n\n참고 자료:\n{context}"
            if context
            else f"질문: {user_message}\n\n참고 자료: (없음)"
        )

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        answer = completion.choices[0].message.content or ""

        return {
            "answer": answer,
            "is_general_info": is_general_info,
            "sources": self.to_sources(relevant),
        }
