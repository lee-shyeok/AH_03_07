import hmac
import json
import os
import secrets
import string

from dotenv import load_dotenv

load_dotenv('envs/.local.env')

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import (
    get_db,
    key_access_token_blocklist,
    key_email_send_rate,
    key_email_token,
    key_email_verify_code,
    key_login_fail,
    key_login_lock,
    key_refresh_token,
    key_verify_code_fail,
    key_verify_code_lock,
    redis_client,
)
from models import User
from schemas import (
    EmailVerifyConfirmRequest,
    EmailVerifyResponse,
    EmailVerifySendRequest,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserBrief,
)
from security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_id,
    hash_password,
    verify_password,
)

EMAIL_VERIFY_CODE_EXPIRE  = int(os.getenv("EMAIL_VERIFY_CODE_EXPIRE_SECONDS", 300))
EMAIL_TOKEN_EXPIRE        = int(os.getenv("EMAIL_TOKEN_EXPIRE_SECONDS", 1800))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14))
LOGIN_FAIL_MAX            = int(os.getenv("LOGIN_FAIL_MAX", 5))
LOGIN_LOCK_SECONDS        = int(os.getenv("LOGIN_LOCK_SECONDS", 600))

VERIFY_FAIL_MAX     = 5
VERIFY_LOCK_SECONDS = 300
EMAIL_SEND_RATE_MAX    = 5
EMAIL_SEND_RATE_WINDOW = 300

_DUMMY_HASH = "$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234"
assert len(_DUMMY_HASH) == 60, "dummy hash must be 60 chars"

router = APIRouter()


# ── 이메일 인증코드 발송 ──────────────────────────────────

@router.post("/email-verify/send", summary="REQ-USER-002: 인증코드 발송")
def send_email_verify_code(body: EmailVerifySendRequest):
    email = str(body.email)

    pipe = redis_client.pipeline()
    pipe.incr(key_email_send_rate(email))
    pipe.expire(key_email_send_rate(email), EMAIL_SEND_RATE_WINDOW)
    results = pipe.execute()
    send_count = results[0]

    if send_count > EMAIL_SEND_RATE_MAX:
        raise HTTPException(
            status_code=429,
            detail="인증코드 발송 횟수를 초과했습니다. 잠시 후 다시 시도해주세요."
        )

    code = "".join(secrets.choice(string.digits) for _ in range(6))
    redis_client.setex(key_email_verify_code(email), EMAIL_VERIFY_CODE_EXPIRE, code)

    try:
        from utils.email import send_verification_email
        send_verification_email(email, code)
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        redis_client.delete(key_email_verify_code(email))
        raise HTTPException(
            status_code=503,
            detail="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요."
        )

    return {"message": "인증코드가 발송되었습니다."}


# ── 이메일 인증코드 확인 ──────────────────────────────────

@router.post("/email-verify/confirm", response_model=EmailVerifyResponse, summary="REQ-USER-002: 인증코드 확인")
def confirm_email_verify_code(body: EmailVerifyConfirmRequest):
    email = str(body.email)

    if redis_client.exists(key_verify_code_lock(email)):
        ttl = redis_client.ttl(key_verify_code_lock(email))
        raise HTTPException(
            status_code=429,
            detail=f"인증 시도가 너무 많습니다. {ttl}초 후 다시 시도해주세요."
        )

    saved = redis_client.get(key_email_verify_code(email))
    if not saved:
        raise HTTPException(status_code=400, detail="인증코드가 만료되었거나 존재하지 않습니다.")

    if not hmac.compare_digest(saved, body.code):
        fail_count = redis_client.incr(key_verify_code_fail(email))
        redis_client.expire(key_verify_code_fail(email), VERIFY_LOCK_SECONDS)

        if fail_count >= VERIFY_FAIL_MAX:
            redis_client.setex(key_verify_code_lock(email), VERIFY_LOCK_SECONDS, "1")
            redis_client.delete(key_verify_code_fail(email))
            redis_client.delete(key_email_verify_code(email))
            raise HTTPException(status_code=429, detail="인증 시도 횟수를 초과했습니다. 인증코드를 다시 발급받아주세요.")

        raise HTTPException(status_code=400, detail="인증코드가 올바르지 않습니다.")

    redis_client.delete(key_email_verify_code(email))
    redis_client.delete(key_verify_code_fail(email))

    email_token = secrets.token_urlsafe(32)
    redis_client.setex(key_email_token(email_token), EMAIL_TOKEN_EXPIRE, email)

    return EmailVerifyResponse(email_token=email_token)


# ── 회원가입 ──────────────────────────────────────────────

@router.post("/signup", response_model=SignupResponse, status_code=201, summary="REQ-USER-001: 회원가입")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    token_email = redis_client.get(key_email_token(data.email_token))
    if not token_email:
        raise HTTPException(status_code=400, detail="이메일 인증 토큰이 만료되었거나 유효하지 않습니다.")
    if not hmac.compare_digest(token_email, str(data.email)):
        raise HTTPException(status_code=400, detail="이메일 인증 토큰과 이메일이 일치하지 않습니다.")

    if db.query(User).filter(User.email == str(data.email)).first():
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")

    user = User(
        email=str(data.email),
        password=hash_password(data.password),
        name=data.name,
        birth_date=data.birth_date,
        gender=data.gender,
        phone_number=data.phone_number,
        is_email_verified=True,
        agreed_terms=data.agreed_terms,
        agreed_privacy=data.agreed_privacy,
        agreed_sensitive_medical=data.agreed_sensitive_medical,
    )
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
    db.refresh(user)

    access_token, _ = create_access_token(user.id)
    refresh_token, refresh_jti = create_refresh_token(user.id)
    redis_client.setex(
        key_refresh_token(user.id),
        REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        json.dumps({"jti": refresh_jti, "token": refresh_token}),
    )
    redis_client.delete(key_email_token(data.email_token))

    return SignupResponse(user_id=user.id, access_token=access_token, refresh_token=refresh_token)


# ── 로그인 ────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse, summary="REQ-USER-003: 로그인")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    email = str(data.email)

    if redis_client.exists(key_login_lock(email)):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    password_ok = (
        verify_password(data.password, user.password)
        if user
        else verify_password(data.password, _DUMMY_HASH)
    )

    if not user or not password_ok:
        pipe = redis_client.pipeline()
        pipe.incr(key_login_fail(email))
        pipe.expire(key_login_fail(email), LOGIN_LOCK_SECONDS)
        results = pipe.execute()
        fail_count = results[0]

        if fail_count >= LOGIN_FAIL_MAX:
            redis_client.setex(key_login_lock(email), LOGIN_LOCK_SECONDS, "1")
            redis_client.delete(key_login_fail(email))

        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    redis_client.delete(key_login_fail(email))

    access_token, _ = create_access_token(user.id)
    refresh_token, refresh_jti = create_refresh_token(user.id)
    redis_client.setex(
        key_refresh_token(user.id),
        REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        json.dumps({"jti": refresh_jti, "token": refresh_token}),
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserBrief.model_validate(user),
    )


# ── 토큰 갱신 ────────────────────────────────────────────

@router.post("/token/refresh", response_model=TokenRefreshResponse, summary="REQ-USER-004: 토큰 갱신")
def token_refresh(body: TokenRefreshRequest):
    from jose import JWTError

    try:
        payload = decode_token(body.refresh_token, "refresh")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다. 다시 로그인해주세요.")

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다. 다시 로그인해주세요.")

    incoming_jti = payload.get("jti", "")

    stored_raw = redis_client.get(key_refresh_token(user_id))
    if not stored_raw:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다. 다시 로그인해주세요.")

    try:
        stored = json.loads(stored_raw)
    except (json.JSONDecodeError, ValueError):
        redis_client.delete(key_refresh_token(user_id))
        raise HTTPException(status_code=401, detail="세션 데이터가 손상되었습니다. 다시 로그인해주세요.")

    if not hmac.compare_digest(stored["jti"], incoming_jti):
        redis_client.delete(key_refresh_token(user_id))
        raise HTTPException(status_code=401, detail="토큰 재사용이 감지되었습니다. 다시 로그인해주세요.")

    new_access, _ = create_access_token(user_id)
    new_refresh, new_jti = create_refresh_token(user_id)
    redis_client.setex(
        key_refresh_token(user_id),
        REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        json.dumps({"jti": new_jti, "token": new_refresh}),
    )

    return TokenRefreshResponse(access_token=new_access, refresh_token=new_refresh)


# ── 로그아웃 ──────────────────────────────────────────────

@router.post("/logout", status_code=204, summary="REQ-USER-005: 로그아웃")
def logout(request: Request, user_id: int = Depends(get_current_user_id)):
    import time

    from jose import JWTError

    redis_client.delete(key_refresh_token(user_id))

    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        payload = decode_token(raw_token, "access")
        jti = payload["jti"]
        remaining = max(int(payload["exp"]) - int(time.time()), 1)
        redis_client.setex(key_access_token_blocklist(jti), remaining, "1")
    except JWTError:
        pass
