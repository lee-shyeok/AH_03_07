import re
from dataclasses import dataclass

import fitz  # PyMuPDF

_SECTION_PATTERNS = [
    re.compile(r"^제\s*\d+\s*장"),
    re.compile(r"^\d+\.\d+\s"),
    re.compile(r"^[IVX]+\.\s"),
]

# ── 노이즈 인라인 패턴 (블록 내 해당 부분만 제거, 본문 유지) ─────────────────
_NOISE_INLINE_PATTERNS: list[re.Pattern] = [
    # 날짜+시간 타임스탬프: "2026. 5. 26.  오전  3:29"  (PDF 웹 인쇄 헤더)
    re.compile(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?\s*(?:오전|오후)\s*\d{1,2}:\d{2}"),
    # 날짜만: "2026. 5. 26."
    re.compile(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\."),
    # 시간만: "오전 3:29"  (타임스탬프 분할 잔여)
    re.compile(r"(?:오전|오후)\s*\d{1,2}:\d{2}"),
    # 페이지 비율 마커: "6 페이지 /11 페이지"
    re.compile(r"\d+\s*페이지\s*/\s*\d+\s*페이지"),
    # URL
    re.compile(r"https?://\S+"),
]

_MIN_CLEAN_CHARS = 30  # 정제 후 최소 유효 내용 길이

# 저자 목록 블록 탐지: 한국어 없고 "대문자시작 이름, 번호" 패턴이 3회 이상
# 중간이니셜(M., St.) 처리를 위해 [\w\.\s\-] 사용
_AUTHOR_LIST_RE = re.compile(r"(?:[A-Z][A-Za-z][\w\.\s\-]*,?\s*\d+\b\s*){3,}")


def _clean_block_text(text: str) -> str:
    """블록 텍스트에서 노이즈 패턴만 제거. 본문 내용은 변경하지 않는다."""
    for pat in _NOISE_INLINE_PATTERNS:
        text = pat.sub(" ", text)
    return " ".join(text.split())


def _is_noise_block(raw: str, cleaned: str) -> bool:
    """블록 전체가 노이즈인지 판단.

    - 정제 후 유효 내용이 _MIN_CLEAN_CHARS 미만이면 노이즈
    - 한국어가 없고 저자 목록 패턴이면 서지정보 노이즈
    """
    if len(cleaned) < _MIN_CLEAN_CHARS:
        return True
    has_korean = bool(re.search(r"[가-힣]", cleaned))
    if not has_korean and _AUTHOR_LIST_RE.search(cleaned):
        return True
    return False


@dataclass
class ParsedBlock:
    text: str
    page_number: int
    font_size: float


def check_pdf_safety(pdf_bytes: bytes) -> None:
    """JavaScript 액션이 포함된 PDF면 ValueError를 발생시킨다."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for xref in range(1, doc.xref_length()):
            try:
                obj_str = doc.xref_object(xref)
                if "/JavaScript" in obj_str or "/JS " in obj_str:
                    raise ValueError("악성 콘텐츠 감지: JavaScript 액션 포함")
            except (fitz.mupdf.FzErrorBase, RuntimeError):
                continue
    finally:
        doc.close()


def extract_blocks(pdf_bytes: bytes) -> list[ParsedBlock]:
    """PDF에서 텍스트 블록 목록을 추출한다. 파싱 전 안전 검사를 수행한다.

    노이즈 블록(타임스탬프·페이지 마커·URL·저자 목록)은 적재 전 제거한다.
    """
    check_pdf_safety(pdf_bytes)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks: list[ParsedBlock] = []
    try:
        for page_num, page in enumerate(doc, start=1):
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                spans = [span for line in block["lines"] for span in line["spans"]]
                raw = " ".join(s["text"] for s in spans).strip()
                font_size = max((s["size"] for s in spans), default=0.0)
                if not raw:
                    continue
                cleaned = _clean_block_text(raw)
                if _is_noise_block(raw, cleaned):
                    continue
                blocks.append(ParsedBlock(text=cleaned, page_number=page_num, font_size=font_size))
    finally:
        doc.close()
    return blocks


def detect_section_title(text: str, font_size: float, avg_font_size: float) -> str | None:
    """텍스트가 섹션 제목이면 반환하고, 아니면 None을 반환한다."""
    stripped = text.strip()
    # 1차: 폰트 크기 기반
    if avg_font_size > 0 and font_size >= avg_font_size * 1.2:
        return stripped[:200]
    # 2차: 정규식 패턴
    for pattern in _SECTION_PATTERNS:
        if pattern.match(stripped):
            return stripped[:200]
    return None
