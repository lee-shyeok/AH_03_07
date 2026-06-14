import tiktoken

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
_ENCODING_NAME = "cl100k_base"
_ENC = tiktoken.get_encoding(_ENCODING_NAME)

# 메타성 짧은 청크 제외 기준 (노이즈 제거 후 잔여 단편 방지)
_MIN_CHUNK_CHARS = 50


def count_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def chunk_text(text: str) -> list[str]:
    """텍스트를 500토큰 단위로 분할한다. 오버랩은 50토큰.

    _MIN_CHUNK_CHARS 미만의 메타성 짧은 청크는 결과에서 제외한다.
    """
    if not text.strip():
        return []
    tokens = _ENC.encode(text)
    if len(tokens) <= CHUNK_SIZE_TOKENS:
        return [text] if len(text.strip()) >= _MIN_CHUNK_CHARS else []

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE_TOKENS, len(tokens))
        chunk = _ENC.decode(tokens[start:end])
        if len(chunk.strip()) >= _MIN_CHUNK_CHARS:
            chunks.append(chunk)
        if end == len(tokens):
            break
        start += CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS
    return chunks
