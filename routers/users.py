import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db, key_access_token_blocklist, key_refresh_token, redis_client
from models import User
from schemas import UpdateUserRequest, UserMeResponse, WithdrawalRequest
from security import decode_token, get_current_user_id, hash_password, verify_password

router = APIRouter()


def _get_user_or_404(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


# ── 내 정보 조회 ──────────────────────────────────────────

@router.get("/me", response_model=UserMeResponse, summary="REQ-USER-006: 내 정보 조회")
def get_me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return _get_user_or_404(user_id, db)


# ── 내 정보 수정 ──────────────────────────────────────────

@router.patch("/me", response_model=UserMeResponse, summary="REQ-USER-007: 내 정보 수정")
def update_me(
    data: UpdateUserRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = _get_user_or_404(user_id, db)

    # 비밀번호 변경
    if data.new_password:
        if not verify_password(data.current_password, user.password):
            raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
        user.password = hash_password(data.new_password)

    if data.name is not None:
        user.name = data.name
    if data.phone_number is not None:
        user.phone_number = data.phone_number
    if data.profile_image_url is not None:
        user.profile_image_url = data.profile_image_url
    if data.chronic_diseases is not None:
        user.chronic_diseases = data.chronic_diseases
    if data.allergy_info is not None:
        user.allergy_info = data.allergy_info

    db.commit()
    db.refresh(user)
    return user


# ── 회원탈퇴 ──────────────────────────────────────────────

@router.delete("/me", status_code=204, summary="REQ-USER-008: 회원탈퇴")
def withdraw(
    data: WithdrawalRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    - 계정: Soft Delete (deleted_at 설정)
    - 의료 데이터 삭제는 CASCADE 또는 별도 배치 처리 필요
    - 현재 세션 즉시 종료
    """
    from jose import JWTError

    user = _get_user_or_404(user_id, db)

    user.deleted_at = datetime.now(UTC)
    user.is_active = False
    if data.withdrawal_reason:
        user.withdrawal_reason = data.withdrawal_reason

    db.commit()

    # 세션 종료 (로그아웃)
    redis_client.delete(key_refresh_token(user_id))
    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        payload = decode_token(raw_token, "access")
        jti = payload["jti"]
        remaining = max(int(payload["exp"]) - int(time.time()), 1)
        redis_client.setex(key_access_token_blocklist(jti), remaining, "1")
    except JWTError:
        pass
