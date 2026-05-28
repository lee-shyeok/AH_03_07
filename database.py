import os

import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv('envs/.local.env')
load_dotenv('envs/.local.env')
print("REDIS_URL:", os.getenv("REDIS_URL"))
# ── MySQL ─────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("환경변수 DATABASE_URL이 설정되지 않았습니다.")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Redis ─────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("환경변수 REDIS_URL이 설정되지 않았습니다.")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ── Redis Key 함수 ────────────────────────────────────────
def key_email_verify_code(email: str) -> str:
    return f"email:verify_code:{email}"

def key_email_token(token: str) -> str:
    return f"email:token:{token}"

def key_refresh_token(user_id: int) -> str:
    return f"auth:refresh:{user_id}"

def key_access_token_blocklist(jti: str) -> str:
    return f"auth:blocklist:{jti}"

def key_login_fail(email: str) -> str:
    return f"auth:login_fail:{email}"

def key_login_lock(email: str) -> str:
    return f"auth:login_lock:{email}"

def key_verify_code_fail(email: str) -> str:
    return f"email:verify_fail:{email}"

def key_verify_code_lock(email: str) -> str:
    return f"email:verify_lock:{email}"

def key_email_send_rate(email: str) -> str:
    return f"email:send_rate:{email}"
