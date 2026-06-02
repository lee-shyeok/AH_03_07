from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RateLimitTier:
    name: str
    limit: int
    patterns: list[tuple[str, str]] = field(default_factory=list)


TIERS: list[RateLimitTier] = [
    RateLimitTier(
        "llm",
        30,
        [
            ("POST", "/api/v1/chat/sessions/"),
            ("POST", "/api/v1/guide/generate"),
            ("POST", "/api/v1/guide/"),
        ],
    ),
    RateLimitTier(
        "ocr",
        20,
        [
            ("POST", "/api/v1/pills/recognize"),
            ("POST", "/api/v1/medical-documents/"),
        ],
    ),
    RateLimitTier("default", 100),
]


def get_tier(method: str, path: str) -> RateLimitTier:
    """method + path prefix로 rate limit tier를 결정한다. 매칭 없으면 default 반환."""
    for tier in TIERS[:-1]:
        for m, prefix in tier.patterns:
            if method == m and path.startswith(prefix):
                return tier
    return TIERS[-1]
