from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.users import Gender, UserMode

class UserCreateRequest(BaseModel):
    email: str
    password: str
    name: str
    gender: Gender
    birthday: date
    phone_number: str

class UserUpdateRequest(BaseModel):
    name: str | None = None
    phone_number: str | None = None

class UserModeUpdateRequest(BaseModel):
    mode: UserMode

class UserInfoResponse(BaseModel):
    id: UUID
    email: str
    name: str
    gender: Gender
    birthday: date
    phone_number: str
    mode: UserMode
    is_active: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    gender: Gender
    birthday: date
    phone_number: str
    mode: UserMode
    is_active: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserModeResponse(BaseModel):
    mode: UserMode

    class Config:
        from_attributes = True