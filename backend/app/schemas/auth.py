from pydantic import BaseModel, EmailStr


class VerifyCode(BaseModel):
    email: EmailStr
    code: str


class EmailRequest(BaseModel):
    email: EmailStr
