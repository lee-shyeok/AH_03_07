import asyncio
import sys

sys.path.insert(0, "/app")  # app 패키지 경로 추가

from app.services.knowledge_search import search_knowledge

# ↓↓↓ 본인 PDF 내용에 맞는 질문으로 바꾸세요 ↓↓↓
QUERY = "면역억제제의 부작용은 무엇인가요?"


async def main():
    print(f"🔍 검색어: {QUERY}\n")
    results = await search_knowledge(QUERY, top_k=3)

    if not results:
        print("⚠️  결과 0개 — Qdrant가 비어있어요. PDF를 먼저 업로드하세요.")
        return

    print(f"✅ 청크 {len(results)}개 발견:\n")
    for i, c in enumerate(results, 1):
        print(f"[{i}] 유사도 {c.score:.3f} | 문서 {c.document_id} | {c.page_number}p")
        print(f"    {c.text[:200].strip()}\n")


asyncio.run(main())
