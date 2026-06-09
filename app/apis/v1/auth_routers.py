from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import JSONResponse as Response

from app.core import config
from app.core.config import Env
from app.dtos.auth import (
    EmailVerifyConfirmRequest,
    EmailVerifyConfirmResponse,
    EmailVerifySendRequest,
    EmailVerifySendResponse,
    LoginRequest,
    LoginResponse,
    SignUpRequest,
    TokenRefreshResponse,
)
from app.services.auth import AuthService
from app.services.email_verify_service import confirm_code, generate_email_token, send_verification_code
from app.services.jwt import JwtService

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    await auth_service.signup(request)
    return Response(content={"detail": "회원가입이 성공적으로 완료되었습니다."}, status_code=status.HTTP_201_CREATED)


@auth_router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> Response:
    user = await auth_service.authenticate(request)
    tokens = await auth_service.login(user)
    resp = Response(
        content=LoginResponse(access_token=str(tokens["access_token"])).model_dump(), status_code=status.HTTP_200_OK
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(tokens["refresh_token"]),
        httponly=True,
        secure=True if config.ENV == Env.PROD else False,
        domain=config.COOKIE_DOMAIN or None,
        expires=tokens["access_token"].payload["exp"],
    )
    return resp


@auth_router.get("/token/refresh", response_model=TokenRefreshResponse, status_code=status.HTTP_200_OK)
async def token_refresh(
    jwt_service: Annotated[JwtService, Depends(JwtService)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is missing.")
    access_token = jwt_service.refresh_jwt(refresh_token)
    return Response(
        content=TokenRefreshResponse(access_token=str(access_token)).model_dump(), status_code=status.HTTP_200_OK
    )


@auth_router.post("/email-verify/send", response_model=EmailVerifySendResponse, status_code=status.HTTP_200_OK)
async def email_verify_send(
    request: EmailVerifySendRequest,
) -> dict:
    code = await send_verification_code(request.email)
    # 개발환경에서는 응답에 코드 포함 (배포 전 제거)
    from app.core import config as cfg
    from app.core.config import Env

    dev_code = code if cfg.ENV != Env.PROD else None
    return {"message": "인증코드가 발송되었습니다.", "dev_code": dev_code}


@auth_router.post("/email-verify/confirm", response_model=EmailVerifyConfirmResponse, status_code=status.HTTP_200_OK)
async def email_verify_confirm(
    request: EmailVerifyConfirmRequest,
) -> dict:
    valid = await confirm_code(request.email, request.code)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증코드가 올바르지 않거나 만료되었습니다.",
        )
    token = generate_email_token(request.email)
    return {"email_token": token, "message": "이메일 인증이 완료되었습니다."}
