"""REQ-FEED-002 가명처리 모듈 (개인정보보호법 §28-2).

처리 원칙:
- 사용자 식별자: HMAC-SHA256 일방향 해시 (복호화 불가)
- 약품명/진단명: AES-128-GCM 암호화 (매핑 키 = ANONYMIZATION_SECRET_KEY)
- 매핑 키(.env)와 가명정보(DB)를 물리적 분리 → KMS 통합 가능 구조
"""

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core import config

_HMAC_KEY: bytes = config.ANONYMIZATION_SECRET_KEY.encode()

# AES-GCM은 16바이트(128-bit) 키 사용
_AES_KEY: bytes = hashlib.sha256(config.ANONYMIZATION_SECRET_KEY.encode()).digest()[:16]


def pseudonymize_user_id(user_id: str) -> str:
    """사용자 식별자를 HMAC-SHA256 일방향 해시로 변환."""
    digest = hmac.new(_HMAC_KEY, user_id.encode(), hashlib.sha256).hexdigest()
    return f"u_{digest[:16]}"


def encrypt_term(term: str) -> str:
    """약품명/진단명을 AES-128-GCM으로 암호화.

    복호화 키는 ANONYMIZATION_SECRET_KEY (.env) 에만 존재.
    반환값: base64url 인코딩된 (nonce + ciphertext).
    """
    aesgcm = AESGCM(_AES_KEY)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, term.encode(), None)
    raw = nonce + ct
    return base64.urlsafe_b64encode(raw).decode()


def decrypt_term(token: str) -> str:
    """encrypt_term 역연산 (매핑 키 보유 시스템에서만 사용)."""
    raw = base64.urlsafe_b64decode(token.encode())
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(_AES_KEY)
    return aesgcm.decrypt(nonce, ct, None).decode()


def pseudonymize_text(text: str, terms: list[str]) -> str:
    """자유 텍스트에서 지정 용어를 암호화 토큰으로 치환."""
    for term in terms:
        if term and term in text:
            token = encrypt_term(term)
            text = text.replace(term, f"[ENC:{token[:8]}]")
    return text


def describe_level(user_hashed: bool, terms_encrypted: bool) -> str:
    """AuditLog / ModelImprovementDataset.pseudonymization_level 기록용."""
    parts = []
    if user_hashed:
        parts.append("user_id=hmac_sha256")
    if terms_encrypted:
        parts.append("drug_name=aes128gcm, diagnosis=aes128gcm")
    return ", ".join(parts) if parts else "none"
