import os
import uuid
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import key_access_token_blocklist, redis_client

load_dotenv()

# SECRET_KEY 기본값 제거 — 없으면 서버 시작 시 즉시 에러
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("환경변수 SECRET_KEY가 설정되지 않았습니다.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _now_utc():
    return datetime.now(UTC)


def create_access_token(user_id: int) -> tuple[str, str]:
    """Access Token 생성. (token, jti) 반환"""
    jti = str(uuid.uuid4())
    expire = _now_utc() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), jti


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """Refresh Token 생성. (token, jti) 반환"""
    jti = str(uuid.uuid4())
    expire = _now_utc() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), jti


def decode_token(token: str, token_type: str = "access") -> dict:
    """토큰 디코딩 + 타입 검증. 실패 시 JWTError"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != token_type:
        raise JWTError("토큰 타입 불일치")
    return payload


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Access Token 검증 → user_id 반환.
    만료·위조·로그아웃된 토큰이면 401.
    """
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인이 필요합니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, "access")
    except JWTError:
        raise exc

    jti = payload.get("jti")
    user_id = payload.get("sub")
    if not jti or not user_id:
        raise exc

    # 로그아웃된 토큰(차단 목록) 확인
    if redis_client.exists(key_access_token_blocklist(jti)):
        raise exc

    return int(user_id)
