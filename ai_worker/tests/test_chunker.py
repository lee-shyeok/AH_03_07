from ai_worker.utils.chunker import CHUNK_SIZE_TOKENS, chunk_text, count_tokens


def test_chunk_empty_string():
    assert chunk_text("") == []


def test_chunk_whitespace_only():
    assert chunk_text("   \n  ") == []


def test_chunk_short_text_single_chunk():
    # _MIN_CHUNK_CHARS 이상의 실질 내용 → 단일 청크 반환
    text = "루푸스 환자는 자외선 차단제를 매일 사용하는 것이 중요합니다. 정기적인 의료 검진도 필요합니다."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_filters_very_short_metadata():
    # _MIN_CHUNK_CHARS 미만 → 메타성 단편으로 간주, 제외
    assert chunk_text("PICO 12.a") == []


def test_chunk_long_text_multiple_chunks():
    # 영문 "word " 한 단어 ≈ 1토큰. 600개면 500토큰 초과
    text = "word " * 600
    chunks = chunk_text(text)
    assert len(chunks) >= 2


def test_chunk_size_never_exceeds_limit():
    text = "word " * 600
    chunks = chunk_text(text)
    for chunk in chunks:
        assert count_tokens(chunk) <= CHUNK_SIZE_TOKENS


def test_chunk_overlap_covers_all_tokens():
    text = "word " * 600
    chunks = chunk_text(text)
    # 오버랩 덕분에 총 토큰 수가 원본보다 많거나 같아야 함
    total = sum(count_tokens(c) for c in chunks)
    assert total >= count_tokens(text)


def test_count_tokens_english():
    # "hello world" → cl100k_base에서 2토큰
    assert count_tokens("hello world") == 2


def test_count_tokens_empty():
    assert count_tokens("") == 0
