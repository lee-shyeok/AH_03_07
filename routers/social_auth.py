import json
import os
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, key_refresh_token, redis_client
from models import User
from security import create_access_token, create_refresh_token, hash_password

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14))

# 구글 클라이언트 ID
GOOGLE_CLIENT_IDS = [
    os.getenv("GOOGLE_WEB_CLIENT_ID", "225363408316-tc94smckivafff92d7tunfjd07g7fmn6.apps.googleusercontent.com"),
    os.getenv("GOOGLE_ANDROID_CLIENT_ID", "225363408316-20i9n98triv1b3u3pe48il7qja07lpbb.apps.googleusercontent.com"),
    os.getenv("GOOGLE_IOS_CLIENT_ID", "225363408316-j3umn1obrt11v1lh299dte10e87sfv4b.apps.googleusercontent.com"),
]

# 네이버 클라이언트 정보
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "MHBLv1HklEH4MDoNoHYF")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "qQoYInS5nE")

router = APIRouter()


# ── 요청/응답 모델 ──────────────────────────────────────

class GoogleLoginRequest(BaseModel):
    id_token: str | None = None
    access_token: str | None = None


class NaverLoginRequest(BaseModel):
    code: str        # 네이버에서 받은 인가 코드
    state: str       # CSRF 방지용 state


class SocialLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    is_new_user: bool


# ── 구글 토큰 검증 ──────────────────────────────────────

async def verify_google_token(id_token: str | None = None, access_token: str | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        if id_token:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="유효하지 않은 구글 ID 토큰입니다.")
            token_info = response.json()
            if token_info.get("aud") not in GOOGLE_CLIENT_IDS:
                raise HTTPException(status_code=401, detail="허용되지 않은 클라이언트입니다.")
            if token_info.get("email_verified") != "true":
                raise HTTPException(status_code=401, detail="이메일이 인증되지 않은 구글 계정입니다.")
            return token_info
        elif access_token:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="유효하지 않은 구글 액세스 토큰입니다.")
            return response.json()
        else:
            raise HTTPException(status_code=400, detail="구글 토큰이 없습니다.")


# ── 공통 유저 처리 ──────────────────────────────────────

def get_or_create_user(db: Session, email: str, name: str, social_provider: str, social_id: str):
    user = db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None)
    ).first()

    is_new_user = False

    if not user:
        is_new_user = True
        user = User(
            email=email,
            password=hash_password(secrets.token_urlsafe(32)),
            name=name,
            is_email_verified=True,
            agreed_terms=True,
            agreed_privacy=True,
            agreed_sensitive_medical=True,
            social_provider=social_provider,
            social_id=social_id,
        )
        db.add(user)
        try:
            db.commit()
        except Exception:
            db.rollback()
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=500, detail="회원가입 처리 중 오류가 발생했습니다.")
        db.refresh(user)

    return user, is_new_user


def issue_tokens(user_id: int) -> tuple[str, str]:
    access_token, _ = create_access_token(user_id)
    refresh_token, refresh_jti = create_refresh_token(user_id)
    redis_client.setex(
        key_refresh_token(user_id),
        REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        json.dumps({"jti": refresh_jti, "token": refresh_token}),
    )
    return access_token, refresh_token


# ── 구글 로그인 ──────────────────────────────────────────

@router.post("/google", response_model=SocialLoginResponse, summary="구글 소셜 로그인/회원가입")
async def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    token_info = await verify_google_token(
        id_token=body.id_token,
        access_token=body.access_token,
    )

    email = token_info.get("email")
    name = token_info.get("name", email.split("@")[0] if email else "사용자")
    google_sub = token_info.get("sub")

    if not email:
        raise HTTPException(status_code=400, detail="구글 계정에서 이메일을 가져올 수 없습니다.")

    user, is_new_user = get_or_create_user(db, email, name, "google", google_sub)
    access_token, refresh_token = issue_tokens(user.id)

    return SocialLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new_user,
    )


# ── 네이버 로그인 ─────────────────────────────────────────

@router.post("/naver", response_model=SocialLoginResponse, summary="네이버 소셜 로그인/회원가입")
async def naver_login(body: NaverLoginRequest, db: Session = Depends(get_db)):
    # 1. 인가 코드로 액세스 토큰 발급
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": NAVER_CLIENT_ID,
                "client_secret": NAVER_CLIENT_SECRET,
                "code": body.code,
                "state": body.state,
            }
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=401, detail="네이버 토큰 발급에 실패했습니다.")

    token_data = token_response.json()
    naver_access_token = token_data.get("access_token")

    if not naver_access_token:
        raise HTTPException(status_code=401, detail="네이버 액세스 토큰을 가져올 수 없습니다.")

    # 2. 액세스 토큰으로 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        profile_response = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {naver_access_token}"}
        )

    if profile_response.status_code != 200:
        raise HTTPException(status_code=401, detail="네이버 사용자 정보 조회에 실패했습니다.")

    profile_data = profile_response.json()
    response_data = profile_data.get("response", {})

    email = response_data.get("email")
    name = response_data.get("name", "네이버사용자")
    naver_id = response_data.get("id")

    if not email:
        raise HTTPException(status_code=400, detail="네이버 계정에서 이메일을 가져올 수 없습니다.")

    user, is_new_user = get_or_create_user(db, email, name, "naver", naver_id)
    access_token, refresh_token = issue_tokens(user.id)

    return SocialLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new_user,
    )
