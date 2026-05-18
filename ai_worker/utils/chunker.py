import tiktoken

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
_ENCODING_NAME = "cl100k_base"


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding(_ENCODING_NAME)
    return len(enc.encode(text))


def chunk_text(text: str) -> list[str]:
    """텍스트를 500토큰 단위로 분할한다. 오버랩은 50토큰."""
    if not text.strip():
        return []
    enc = tiktoken.get_encoding(_ENCODING_NAME)
    tokens = enc.encode(text)
    if len(tokens) <= CHUNK_SIZE_TOKENS:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE_TOKENS, len(tokens))
        chunks.append(enc.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS
    return chunks
