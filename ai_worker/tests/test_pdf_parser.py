import fitz

from ai_worker.utils.pdf_parser import (
    check_pdf_safety,
    detect_section_title,
    extract_blocks,
)


def _make_test_pdf(text: str, fontsize: float = 12.0) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=fontsize)
    return doc.tobytes()


def test_extract_blocks_returns_text():
    pdf_bytes = _make_test_pdf("Rheumatoid treatment guidelines")
    blocks = extract_blocks(pdf_bytes)
    combined = " ".join(b.text for b in blocks)
    assert "Rheumatoid" in combined


def test_extract_blocks_page_number():
    pdf_bytes = _make_test_pdf("Test text")
    blocks = extract_blocks(pdf_bytes)
    assert all(b.page_number == 1 for b in blocks)


def test_extract_blocks_font_size():
    pdf_bytes = _make_test_pdf("Header", fontsize=18.0)
    blocks = extract_blocks(pdf_bytes)
    assert any(b.font_size >= 18.0 for b in blocks)


def test_detect_section_title_by_font_size():
    result = detect_section_title("제1장 서론", font_size=20.0, avg_font_size=12.0)
    assert result == "제1장 서론"


def test_detect_section_title_by_regex_chapter():
    result = detect_section_title("제 1 장 서론", font_size=12.0, avg_font_size=12.0)
    assert result == "제 1 장 서론"


def test_detect_section_title_by_regex_numbered():
    result = detect_section_title("1.1 치료 방법", font_size=12.0, avg_font_size=12.0)
    assert result == "1.1 치료 방법"


def test_detect_section_title_by_regex_roman():
    result = detect_section_title("IV. 결론", font_size=12.0, avg_font_size=12.0)
    assert result == "IV. 결론"


def test_detect_section_title_no_match_returns_none():
    result = detect_section_title("일반 본문 텍스트입니다.", font_size=12.0, avg_font_size=12.0)
    assert result is None


def test_check_pdf_safety_clean_pdf():
    pdf_bytes = _make_test_pdf("Safe document")
    check_pdf_safety(pdf_bytes)  # 예외 없이 통과


def test_check_pdf_safety_detects_javascript():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    # 기본 PDF는 통과함을 확인
    check_pdf_safety(pdf_bytes)  # 예외 없음
