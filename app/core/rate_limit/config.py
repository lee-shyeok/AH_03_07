from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RateLimitTier:
    name: str
    limit: int  # 분당 최대 요청 수 (fixed-window 60s)
    patterns: list[tuple[str, str]] = field(default_factory=list)


_DEFAULT_TIER = RateLimitTier("default", 100)

TIERS: list[RateLimitTier] = [
    RateLimitTier(
        name="llm",
        limit=30,
        patterns=[
            ("POST", "/api/v1/chat/sessions/"),
            ("POST", "/api/v1/guide/generate"),
            ("POST", "/api/v1/guide/"),
        ],
    ),
    RateLimitTier(
        name="ocr",
        limit=20,
        patterns=[
            ("POST", "/api/v1/pills/recognize"),
            ("POST", "/api/v1/medical-documents/"),
        ],
    ),
]


def get_tier(method: str, path: str) -> RateLimitTier:
    """method + path prefix로 rate limit tier를 결정한다. 매칭 없으면 default 반환."""
    for tier in TIERS:
        for m, prefix in tier.patterns:
            if method == m and path.startswith(prefix):
                return tier
    return _DEFAULT_TIER
