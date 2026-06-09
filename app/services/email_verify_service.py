"""REQ-USER-002 이메일 인증 서비스 (로컬 개발용: 메모리 저장 + 콘솔 출력)"""
from __future__ import annotations

import logging
import random
import string
import time

from app.core import config
from app.core.config import Env

logger = logging.getLogger(__name__)

# 로컬 개발용: 인메모리 저장소 {email: (code, expires_at)}
# 프로덕션에서는 Redis로 교체
_store: dict[str, tuple[str, float]] = {}

CODE_TTL = 300  # 5분
CODE_LEN = 6


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=CODE_LEN))


async def send_verification_code(email: str) -> str:
    """인증코드 생성 및 발송 (로컬: 콘솔 출력, 프로덕션: Gmail SMTP)"""
    code = _generate_code()
    _store[email] = (code, time.time() + CODE_TTL)

    if config.ENV == Env.PROD:
        # TODO: Gmail SMTP 연동
        # await _send_gmail(email, code)
        logger.info("PROD 모드: Gmail SMTP 미설정 — 콘솔 출력으로 대체")

    logger.warning(f"[DEV] 이메일 인증코드 | {email} → {code}")
    return code


async def confirm_code(email: str, code: str) -> bool:
    """인증코드 검증"""
    entry = _store.get(email)
    if not entry:
        return False
    stored_code, expires_at = entry
    if time.time() > expires_at:
        del _store[email]
        return False
    if stored_code != code:
        return False
    del _store[email]
    return True


def generate_email_token(email: str) -> str:
    """검증 완료 후 회원가입용 단기 토큰 (단순 구현)"""
    import base64
    import time as _t
    raw = f"{email}:{int(_t.time()) + 600}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_email_token(token: str, email: str) -> bool:
    """회원가입 시 email_token 검증"""
    try:
        import base64
        import time as _t
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        token_email, expires = raw.rsplit(":", 1)
        return token_email == email and _t.time() < int(expires)
    except Exception:
        return False
