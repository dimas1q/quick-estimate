from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    login: str = Field(..., min_length=3)
    name: str | None = None
    company: str | None = None


class UserCreate(UserBase):
    login: str = Field(..., min_length=3)
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    is_admin: bool
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    login: str = Field(..., min_length=3)
    email: EmailStr
    name: str | None = None
    company: str | None = None


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class VerifyCode(BaseModel):
    email: EmailStr
    code: str


class EmailRequest(BaseModel):
    email: EmailStr
