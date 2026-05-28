import re
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from models import GenderEnum

# [수정 6] \S{8,} — 공백 문자 차단
PASSWORD_REGEX = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?])\S{8,}$')
PHONE_REGEX = re.compile(r"^01[0-9]-?\d{3,4}-?\d{4}$")

# ── 이메일 인증 ───────────────────────────────────────────


class EmailVerifySendRequest(BaseModel):
    email: EmailStr


class EmailVerifyConfirmRequest(BaseModel):
    email: EmailStr
    code: str

    @field_validator("code")
    @classmethod
    def code_format(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("인증코드는 6자리 숫자여야 합니다.")
        return v


class EmailVerifyResponse(BaseModel):
    email_token: str
    message: str = "이메일 인증이 완료되었습니다."


# ── 회원가입 ──────────────────────────────────────────────


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    password_confirm: str
    name: str
    birth_date: date | None = None
    gender: GenderEnum | None = None
    phone_number: str | None = None
    email_token: str

    agreed_terms: bool
    agreed_privacy: bool
    agreed_sensitive_medical: bool

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not PASSWORD_REGEX.match(v):
            raise ValueError("비밀번호는 영문+숫자+특수문자 조합 8자 이상이어야 합니다.")
        return v

    @field_validator("phone_number")
    @classmethod
    def phone_format(cls, v):
        if v and not PHONE_REGEX.match(v):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다. (예: 010-1234-5678)")
        return v

    @field_validator("name")
    @classmethod
    def name_length(cls, v):
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("이름은 2자 이상이어야 합니다.")
        return stripped

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("비밀번호가 일치하지 않습니다.")
        return self

    @model_validator(mode="after")
    def all_terms_agreed(self):
        if not (self.agreed_terms and self.agreed_privacy and self.agreed_sensitive_medical):
            raise ValueError("필수 약관에 모두 동의해야 합니다.")
        return self


class SignupResponse(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str


# ── 로그인 ────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBrief(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserBrief


# ── 토큰 갱신 ─────────────────────────────────────────────


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str


# ── 내 정보 ───────────────────────────────────────────────


class UserMeResponse(BaseModel):
    id: int
    email: str
    name: str
    birth_date: date | None = None
    gender: GenderEnum | None = None
    phone_number: str | None = None
    profile_image_url: str | None = None
    chronic_diseases: str | None = None
    allergy_info: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    profile_image_url: str | None = None
    chronic_diseases: str | None = None
    allergy_info: str | None = None
    current_password: str | None = None
    new_password: str | None = None
    new_password_confirm: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        # [수정 7] 빈 문자열 / 공백만 입력 차단
        if v is not None:
            stripped = v.strip()
            if len(stripped) < 2:
                raise ValueError("이름은 2자 이상이어야 합니다.")
            return stripped
        return v

    @field_validator("phone_number")
    @classmethod
    def phone_format(cls, v):
        if v and not PHONE_REGEX.match(v):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다. (예: 010-1234-5678)")
        return v

    @field_validator("profile_image_url")
    @classmethod
    def image_url_format(cls, v):
        if v:
            if not (v.startswith("https://") or v.startswith("http://")):
                raise ValueError("프로필 이미지 URL은 http 또는 https로 시작해야 합니다.")
            if len(v) > 500:
                raise ValueError("URL이 너무 깁니다.")
        return v

    @field_validator("chronic_diseases")
    @classmethod
    def chronic_diseases_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("만성질환 정보가 너무 깁니다.")
        return v

    @field_validator("allergy_info")
    @classmethod
    def allergy_info_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("알레르기 정보가 너무 깁니다.")
        return v

    @model_validator(mode="after")
    def validate_password_change(self):
        if any([self.new_password, self.new_password_confirm, self.current_password]):
            if not self.current_password:
                raise ValueError("현재 비밀번호를 입력해주세요.")
            if not self.new_password:
                raise ValueError("새 비밀번호를 입력해주세요.")
            if self.new_password != self.new_password_confirm:
                raise ValueError("새 비밀번호가 일치하지 않습니다.")
            if not PASSWORD_REGEX.match(self.new_password):
                raise ValueError("비밀번호는 영문+숫자+특수문자 조합 8자 이상이어야 합니다.")
        return self


# ── 회원탈퇴 ──────────────────────────────────────────────


class WithdrawalRequest(BaseModel):
    withdrawal_reason: str | None = None

    @field_validator("withdrawal_reason")
    @classmethod
    def reason_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("탈퇴 사유는 500자 이하로 입력해주세요.")
        return v
