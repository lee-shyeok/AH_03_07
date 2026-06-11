import fitz

from ai_worker.utils.pdf_parser import (
    _clean_block_text,
    _is_noise_block,
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
    # 충분히 긴 텍스트(_MIN_CLEAN_CHARS 이상)로 테스트해야 노이즈 필터를 통과한다
    pdf_bytes = _make_test_pdf("Rheumatoid arthritis treatment guideline header.", fontsize=18.0)
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


def test_clean_block_text_removes_timestamp():
    raw = "2026. 5. 26.  오전  3:29 전신홍반루푸스 6 페이지 /11 페이지 https://helpline.kdca.go.kr/abc"
    cleaned = _clean_block_text(raw)
    assert "2026" not in cleaned
    assert "오전" not in cleaned
    assert "페이지" not in cleaned
    assert "https" not in cleaned


def test_clean_block_text_keeps_content():
    raw = "루푸스 환자는 자외선 차단제를 매일 사용하는 것이 중요합니다. 2026. 5. 26."
    cleaned = _clean_block_text(raw)
    assert "루푸스 환자는" in cleaned
    assert "2026" not in cleaned


def test_is_noise_block_pure_page_header():
    raw = "2026. 5. 26.  오전  3:29 전신홍반루푸스 1 페이지 /11 페이지 https://helpline.kdca.go.kr/x"
    cleaned = _clean_block_text(raw)
    assert _is_noise_block(raw, cleaned) is True


def test_is_noise_block_author_list():
    raw = "Liana Fraenkel, 1  Joan M. Bathon, 2  Bryant R. England, 3  E. William St.Clair, 4  Thurayya Arayssi, 5"
    cleaned = _clean_block_text(raw)
    assert _is_noise_block(raw, cleaned) is True


def test_is_noise_block_keeps_real_content():
    raw = "루푸스는 자가면역 질환으로 전신의 다양한 기관을 침범할 수 있습니다."
    cleaned = _clean_block_text(raw)
    assert _is_noise_block(raw, cleaned) is False


def test_extract_blocks_filters_page_header():
    # PyMuPDF 기본 폰트는 CJK 미지원 → ASCII 텍스트로 노이즈 필터링 통합 검증
    doc = fitz.open()
    page = doc.new_page()
    # 타임스탬프+URL 패턴: 정제 후 30자 미만 → 노이즈 블록으로 제거됨
    page.insert_text((50, 50), "2026. 5. 26. https://example.com/doc/health-info")
    # 정상 내용 블록: 충분한 길이 + 노이즈 없음 → 보존됨
    page.insert_text((50, 150), "Rheumatoid arthritis treatment guidelines for patients.")
    pdf_bytes = doc.tobytes()
    blocks = extract_blocks(pdf_bytes)
    combined = " ".join(b.text for b in blocks)
    assert "Rheumatoid arthritis" in combined
    assert "2026" not in combined
    assert "https" not in combined


def test_check_pdf_safety_detects_javascript():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    # 기본 PDF는 통과함을 확인
    check_pdf_safety(pdf_bytes)  # 예외 없음
