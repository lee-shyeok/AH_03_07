import re
from dataclasses import dataclass

import fitz  # PyMuPDF

_SECTION_PATTERNS = [
    re.compile(r"^제\s*\d+\s*장"),
    re.compile(r"^\d+\.\d+\s"),
    re.compile(r"^[IVX]+\.\s"),
]


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
    """PDF에서 텍스트 블록 목록을 추출한다. 파싱 전 안전 검사를 수행한다."""
    check_pdf_safety(pdf_bytes)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks: list[ParsedBlock] = []
    try:
        for page_num, page in enumerate(doc, start=1):
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                spans = [span for line in block["lines"] for span in line["spans"]]
                text = " ".join(s["text"] for s in spans).strip()
                font_size = max((s["size"] for s in spans), default=0.0)
                if text:
                    blocks.append(ParsedBlock(text=text, page_number=page_num, font_size=font_size))
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
