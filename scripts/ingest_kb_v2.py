"""
medical_kb_v2 재인제스트 — 호스트 standalone 스크립트
원본 embedding.py 와 동일한 파이프라인:
  full_text = " ".join(block.text) → chunk_text → _build_chunk_metadata
- 기존 medical_kb 컬렉션은 건드리지 않는다
- medical_kb_v2 새 컬렉션에 적재 (이미 있으면 재생성)
- 실행: python scripts/ingest_kb_v2.py
"""

import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ai_worker.utils.chunker import chunk_text
from ai_worker.utils.pdf_parser import ParsedBlock, detect_section_title, extract_blocks

# ── 설정 ─────────────────────────────────────────────────────────────────────
COLLECTION_V2 = "medical_kb"
VECTOR_SIZE = 1536
EMBEDDING_MODEL = "text-embedding-3-small"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
EMBED_BATCH = 20  # 431 오류 방지를 위해 소배치

# ── 공식 문서 목록 (NFR-SAFE-002: 공식 출처만) ───────────────────────────────
DOCUMENTS = [
    {
        "document_id": 1,
        "path": ROOT / "media/knowledge/11/2021 ACR 류마티스관절염 치료 가이드라인.pdf",
        "source_title": "2021 ACR 류마티스관절염 치료 가이드라인",
        "source_organization": "American College of Rheumatology",
        "published_year": 2021,
    },
    {
        "document_id": 2,
        "path": ROOT / "media/knowledge/7/전신홍반루푸스.pdf",
        "source_title": "전신홍반루푸스",
        "source_organization": "질병관리청",
        "published_year": 2022,
    },
]


def _build_chunk_metadata(
    chunks: list[str],
    blocks: list[ParsedBlock],
    avg_font: float,
) -> list[dict]:
    """원본 embedding.py 의 _build_chunk_metadata 와 동일한 로직."""
    last_section: str | None = None
    result = []
    for i, chunk in enumerate(chunks):
        section = None
        page_num = 1
        for block in blocks:
            if block.text[:40] in chunk:
                page_num = block.page_number
                candidate = detect_section_title(block.text, block.font_size, avg_font)
                if candidate:
                    section = candidate
                    last_section = section
                break
        if section is None:
            section = last_section
        result.append({"chunk_index": i, "section_title": section, "page_number": page_num})
    return result


def _embed_batch_with_retry(client: OpenAI, texts: list[str], retries: int = 3) -> list[list[float]]:
    for attempt in range(retries):
        try:
            resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [item.embedding for item in resp.data]
        except Exception as e:
            if attempt < retries - 1:
                wait = 2**attempt
                print(f"    임베딩 오류 (재시도 {attempt + 1}/{retries}, {wait}s 대기): {e}")
                time.sleep(wait)
            else:
                raise


def _ingest_doc(
    doc_meta: dict,
    qdrant: QdrantClient,
    oai: OpenAI,
) -> int:
    pdf_path: Path = doc_meta["path"]
    doc_id: int = doc_meta["document_id"]
    print(f"\n{'─' * 60}")
    print(f"[문서] {pdf_path.name}")

    pdf_bytes = pdf_path.read_bytes()
    blocks = extract_blocks(pdf_bytes)
    print(f"  파싱 블록 수: {len(blocks)}")

    avg_font = sum(b.font_size for b in blocks) / len(blocks) if blocks else 12.0

    # 원본과 동일: 전체 블록 텍스트를 합친 후 한 번에 청킹
    full_text = " ".join(b.text for b in blocks)
    chunks = chunk_text(full_text)
    chunk_meta = _build_chunk_metadata(chunks, blocks, avg_font)
    print(f"  생성 청크 수: {len(chunks)}")

    if not chunks:
        print("  ⚠️  청크 0개 — 건너뜀")
        return 0

    # 청크 샘플 출력 (처음 3개 + 마지막 1개)
    sample_idx = list(range(min(3, len(chunks))))
    if len(chunks) > 3:
        sample_idx.append(len(chunks) - 1)
    print("  ── 샘플 청크 ──")
    for i in sample_idx:
        m = chunk_meta[i]
        label = f"마지막({i})" if i == len(chunks) - 1 and i >= 3 else str(i)
        print(f"  [{label}] page={m['page_number']}  section={m['section_title']!r}")
        print(f"         {chunks[i][:150]!r}")

    # 임베딩 (소배치 + 재시도)
    print(f"  임베딩 중 (배치={EMBED_BATCH})…")
    embeddings: list[list[float]] = []
    for i in range(0, len(chunks), EMBED_BATCH):
        batch = chunks[i : i + EMBED_BATCH]
        embeddings.extend(_embed_batch_with_retry(oai, batch))
        done = min(i + EMBED_BATCH, len(chunks))
        print(f"    {done}/{len(chunks)} 완료")

    # Qdrant upsert (원본과 동일한 uuid5 포인트 ID)
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}:{meta['chunk_index']}")),
            vector=emb,
            payload={
                "document_id": doc_id,
                "chunk_index": meta["chunk_index"],
                "page_number": meta["page_number"],
                "section_title": meta["section_title"],
                "source_title": doc_meta["source_title"],
                "source_organization": doc_meta["source_organization"],
                "published_year": doc_meta["published_year"],
                "text": chunks[meta["chunk_index"]],
            },
        )
        for meta, emb in zip(chunk_meta, embeddings, strict=False)
    ]
    qdrant.upsert(collection_name=COLLECTION_V2, points=points)
    print(f"  upsert 완료: {len(points)}개")
    return len(points)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY 미설정", file=sys.stderr)
        sys.exit(1)

    oai = OpenAI(api_key=api_key)
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # medical_kb_v2 재생성
    existing = {c.name for c in qdrant.get_collections().collections}
    if COLLECTION_V2 in existing:
        print(f"기존 {COLLECTION_V2} 삭제 후 재생성")
        qdrant.delete_collection(COLLECTION_V2)
    qdrant.create_collection(
        collection_name=COLLECTION_V2,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"컬렉션 생성: {COLLECTION_V2}  (dim={VECTOR_SIZE}, Cosine)")

    if "medical_kb" in existing:
        old_info = qdrant.get_collection("medical_kb")
        print(f"medical_kb 유지됨 (포인트 수: {old_info.points_count})")

    totals: dict[str, int] = {}
    for doc in DOCUMENTS:
        if not doc["path"].exists():
            print(f"⚠️  파일 없음: {doc['path']}", file=sys.stderr)
            continue
        count = _ingest_doc(doc, qdrant, oai)
        totals[doc["path"].name] = count

    info = qdrant.get_collection(COLLECTION_V2)
    print(f"\n{'=' * 60}")
    print(f"medical_kb_v2 적재 완료: 총 {info.points_count}개 포인트")
    for name, cnt in totals.items():
        print(f"  {name}: {cnt}개")

    print("\n검증 체크리스트:")
    print("  [ ] ACR 청크 수 ≥ 4 (2~3 이하면 저자목록 룰 재검토)")
    print("  [ ] 루푸스 청크 수 ≥ 50")
    print("  [ ] 샘플 청크에 타임스탬프·URL·페이지 마커 없음")
    print("  [ ] 샘플 청크에 한국어 의료 내용 있음")
    print("\n검증 통과 후 knowledge_search.py COLLECTION_NAME → medical_kb_v2 로 변경")


if __name__ == "__main__":
    main()
