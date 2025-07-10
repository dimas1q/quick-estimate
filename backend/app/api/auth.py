# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate
from app.schemas.auth import VerifyCode, EmailRequest
from app.utils.auth import authenticate_user
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.email import send_verification_code

router = APIRouter(tags=["auth"])


@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # проверка email
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # проверка логина
    result = await db.execute(select(User).where(User.login == user.login))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Логин уже занят")

    new_user = User(
        login=user.login,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    # OTP generation
    code = f"{random.randint(0, 999999):06d}"
    new_user.hashed_otp = hash_password(code)
    new_user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    new_user.otp_sent_at = datetime.utcnow()

    db.add(new_user)
    await db.commit()
    await send_verification_code(new_user.email, code)
    return {"message": "verification_code_sent"}


@router.post("/verify")
async def verify_code(data: VerifyCode, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_otp:
        raise HTTPException(status_code=400, detail="Код неверный")
    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="Код истёк")
    if not verify_password(data.code, user.hashed_otp):
        raise HTTPException(status_code=400, detail="Код неверный")
    user.is_active = True
    user.hashed_otp = None
    user.otp_expires_at = None
    await db.commit()
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/resend")
async def resend_code(data: EmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or user.is_active:
        raise HTTPException(status_code=400, detail="Неверный запрос")
    if user.otp_sent_at and datetime.utcnow() - user.otp_sent_at < timedelta(seconds=60):
        raise HTTPException(status_code=429, detail="Код уже отправлен")
    code = f"{random.randint(0, 999999):06d}"
    user.hashed_otp = hash_password(code)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    user.otp_sent_at = datetime.utcnow()
    await db.commit()
    await send_verification_code(user.email, code)
    return {"message": "verification_code_sent"}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    identifier = form_data.username
    password = form_data.password

    db_user = await authenticate_user(db, identifier, password)

    if not db_user:
        raise HTTPException(status_code=401, detail="Неверный логин/email или пароль")

    if not db_user.is_active:
        return JSONResponse(status_code=403, content={"detail": "ACCOUNT_INACTIVE", "email": db_user.email})

    token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}
