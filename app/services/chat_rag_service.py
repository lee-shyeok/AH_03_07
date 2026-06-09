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

[절대 금지 사항 — 의료법 제27조 준수]
- 진단·처방·용량 조절·치료 방침 제시를 절대 하지 마세요.
- 사용자 데이터를 근거로 "~해야 한다", "~하세요" 같은 의료적 지시를 하지 마세요.
- 제공된 사용자 정보(약물·활성도)는 대화 맥락 파악에만 사용하며, 임상적 판단의 근거로 쓰지 마세요.

[응답 원칙]
- 제공된 참고 자료에만 근거하여 일반 정보를 안내하세요.
- 관련 자료가 없으면 그렇게 명시하세요.
- 의학적 결정이 필요한 경우 반드시 담당 의료진과의 상담을 권유하세요.
- 한국어로 응답하세요.
- 모든 응답 끝에 "본 내용은 정보 제공 목적이며 의료 진단·처방을 대체하지 않습니다."를 포함하세요."""


class ChatRAGService:
    def filter_by_threshold(
        self, chunks: list[KnowledgeChunk], threshold: float = RAG_SCORE_THRESHOLD
    ) -> list[KnowledgeChunk]:
        return [c for c in chunks if c.score >= threshold]

    def build_context(self, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return ""
        return "\n\n".join(f"[자료 {i + 1}] {c.text}" for i, c in enumerate(chunks))

    def build_user_context(self, user_profile: dict | None) -> str:
        """REQ-CHAT-007: 사용자 프로필·약물·활성도를 시스템 프롬프트에 주입"""
        if not user_profile:
            return ""
        lines = ["[사용자 정보]"]
        if user_profile.get("disease"):
            lines.append(f"- 질환: {user_profile['disease']}")
        if user_profile.get("medications"):
            meds = ", ".join(user_profile["medications"])
            lines.append(f"- 복용 중인 약물: {meds}")
        if user_profile.get("recent_activity"):
            act = user_profile["recent_activity"]
            lines.append(
                f"- 최근 활성도 (통증 {act.get('pain', '-')}/10, "
                f"피로 {act.get('fatigue', '-')}/10, "
                f"불편도 {act.get('difficulty', '-')}/10)"
            )
        if user_profile.get("recent_guide_topics"):
            topics = ", ".join(user_profile["recent_guide_topics"][:3])
            lines.append(f"- 최근 가이드 주제: {topics}")

        # 일반 모드 추가 컨텍스트
        if user_profile.get("recent_records"):
            records = ", ".join(
                f"{r.get('hospital', '')}({r.get('diagnosis', '')})" for r in user_profile["recent_records"]
            )
            lines.append(f"- 최근 진료 기록: {records}")
        if user_profile.get("recent_health_metrics"):
            metrics = ", ".join(
                f"{m.get('type', '')} {m.get('value', '')}" for m in user_profile["recent_health_metrics"]
            )
            lines.append(f"- 최근 건강 수치: {metrics}")

        return "\n".join(lines)

    def to_sources(self, chunks: list[KnowledgeChunk]) -> list[dict]:
        results = []
        for c in chunks:
            title = c.source_title
            if c.source_organization:
                title = f"{title} — {c.source_organization}"
            snippet = c.text[:200] + "..." if len(c.text) > 200 else c.text
            results.append({"title": title, "url": None, "snippet": snippet})
        return results

    async def generate_response(
        self,
        user_message: str,
        top_k: int = 5,
        user_profile: dict | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        chunks = await search_knowledge(user_message, top_k=top_k)
        relevant = self.filter_by_threshold(chunks)
        is_general_info = len(relevant) == 0
        context = self.build_context(relevant)
        user_ctx = self.build_user_context(user_profile)

        system_prompt = SAFETY_SYSTEM_PROMPT
        if user_ctx:
            system_prompt = f"{SAFETY_SYSTEM_PROMPT}\n\n{user_ctx}"

        user_content = (
            f"질문: {user_message}\n\n참고 자료:\n{context}"
            if context
            else f"질문: {user_message}\n\n참고 자료: (없음)"
        )

        # 대화 이력 구성 (최근 10턴)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-10:])
        messages.append({"role": "user", "content": user_content})

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        answer = completion.choices[0].message.content or ""

        return {
            "answer": answer,
            "is_general_info": is_general_info,
            "sources": self.to_sources(relevant),
        }
