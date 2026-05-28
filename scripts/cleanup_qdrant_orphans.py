"""Qdrant 고아 청크 정리 스크립트 (일회성).

유효한 document_id: VALID_DOC_IDS 에 정의된 값만 남기고, 그 외 모든 청크를 삭제한다.

실행:
    # dry-run (삭제 없이 현황만 출력)
    uv run python scripts/cleanup_qdrant_orphans.py

    # 실제 삭제
    uv run python scripts/cleanup_qdrant_orphans.py --execute
"""

import argparse
import sys

from qdrant_client import QdrantClient

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION = "medical_kb"

# MySQL knowledge_base 테이블에 실제로 존재하는 문서 ID
VALID_DOC_IDS = [5, 6]


def _scroll_all(client: QdrantClient) -> list:
    points = []
    offset = None
    while True:
        batch, next_offset = client.scroll(
            collection_name=COLLECTION,
            offset=offset,
            limit=100,
            with_payload=["document_id"],
            with_vectors=False,
        )
        points.extend(batch)
        if next_offset is None:
            break
        offset = next_offset
    return points


def main(execute: bool) -> None:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    print(f"컬렉션: {COLLECTION}")
    print(f"유효 document_id: {VALID_DOC_IDS}")
    print()

    points = _scroll_all(client)
    total = len(points)

    orphans = [p for p in points if p.payload.get("document_id") not in VALID_DOC_IDS]
    valid_count = total - len(orphans)

    print(f"전체 청크: {total}")
    print(f"유효 청크: {valid_count}")
    print(f"고아 청크: {len(orphans)}")

    if not orphans:
        print("\n고아 청크 없음. 종료.")
        return

    # 고아 document_id 목록 출력
    orphan_doc_ids = sorted({p.payload.get("document_id") for p in orphans})
    print(f"고아 document_id 목록: {orphan_doc_ids}")

    if not execute:
        print("\n[dry-run] 실제 삭제하려면 --execute 플래그를 추가하세요.")
        return

    print("\n삭제 진행 중...")
    client.delete(
        collection_name=COLLECTION,
        points_selector=[p.id for p in orphans],
    )

    # 삭제 후 검증
    remaining = _scroll_all(client)
    print(f"삭제 완료. 남은 청크: {len(remaining)}")

    leftover_orphans = [p for p in remaining if p.payload.get("document_id") not in VALID_DOC_IDS]
    if leftover_orphans:
        print(f"[경고] 아직 고아 청크 {len(leftover_orphans)}개 남아 있음.")
        sys.exit(1)
    else:
        print("검증 완료: 고아 청크 없음.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Qdrant 고아 청크 정리")
    parser.add_argument("--execute", action="store_true", help="실제 삭제 수행 (없으면 dry-run)")
    args = parser.parse_args()
    main(execute=args.execute)
