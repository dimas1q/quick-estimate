# api/auth.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, VerifyCode, EmailRequest
from app.utils.auth import authenticate_user
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.otp import generate_code
from app.utils.email import send_verification_code

router = APIRouter(tags=["auth"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def _find_user_by_identifier(db: AsyncSession, identifier: str) -> User | None:
    result = await db.execute(
        select(User).where(or_(User.email == identifier, User.login == identifier))
    )
    return result.scalar_one_or_none()


def _lock_retry_after_seconds(locked_until: datetime, now: datetime) -> int:
    return max(1, int((locked_until - now).total_seconds()))


async def _register_failed_login(db: AsyncSession, user: User, now: datetime) -> bool:
    attempts = int(user.failed_login_attempts or 0) + 1
    if attempts >= settings.AUTH_MAX_FAILED_LOGIN_ATTEMPTS:
        user.failed_login_attempts = 0
        user.locked_until = now + timedelta(minutes=settings.AUTH_LOCK_MINUTES)
        await db.commit()
        return True

    user.failed_login_attempts = attempts
    await db.commit()
    return False


async def _clear_login_locks_if_needed(db: AsyncSession, user: User) -> None:
    if (user.failed_login_attempts or 0) == 0 and not user.locked_until:
        return
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # проверка email
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # проверка логина
    result = await db.execute(select(User).where(User.login == user.login))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Логин уже занят")

    otp = generate_code()
    now = datetime.now(timezone.utc)
    new_user = User(
        login=user.login,
        email=user.email,
        hashed_password=hash_password(user.password),
        is_active=False,
        hashed_otp=hash_password(otp),
        otp_expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        otp_sent_at=now,
    )

    db.add(new_user)
    await db.commit()
    await send_verification_code(user.email, otp)
    await db.refresh(new_user)
    return new_user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    identifier = form_data.username
    password = form_data.password

    db_user = await _find_user_by_identifier(db, identifier)
    now = _now_utc()

    if db_user and db_user.locked_until and db_user.locked_until > now:
        retry_after = _lock_retry_after_seconds(db_user.locked_until, now)
        raise HTTPException(
            status_code=429,
            detail="Слишком много попыток входа. Повторите позже.",
            headers={"Retry-After": str(retry_after)},
        )

    authed_user = await authenticate_user(db, identifier, password)
    if not authed_user:
        if db_user:
            locked_now = await _register_failed_login(db, db_user, now)
            if locked_now and db_user.locked_until:
                retry_after = _lock_retry_after_seconds(db_user.locked_until, now)
                raise HTTPException(
                    status_code=429,
                    detail="Слишком много попыток входа. Повторите позже.",
                    headers={"Retry-After": str(retry_after)},
                )
        raise HTTPException(status_code=401, detail="Неверный логин/email или пароль")

    if not authed_user.is_active:
        return JSONResponse(status_code=403, content={"verify_required": True, "email": authed_user.email})

    await _clear_login_locks_if_needed(db, authed_user)

    token = create_access_token(data={"sub": str(authed_user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/verify")
async def verify_code(data: VerifyCode, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    now = datetime.now(timezone.utc)
    if not user.hashed_otp or not user.otp_expires_at or user.otp_expires_at < now:
        raise HTTPException(status_code=400, detail="Код истёк")

    if not verify_password(data.code, user.hashed_otp):
        raise HTTPException(status_code=400, detail="Неверный код")

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
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.is_active:
        raise HTTPException(status_code=400, detail="Аккаунт уже активирован")

    now = datetime.now(timezone.utc)
    if user.otp_sent_at and (now - user.otp_sent_at).total_seconds() < 60:
        raise HTTPException(status_code=429, detail="Код уже отправлен. Подождите")

    otp = generate_code()
    user.hashed_otp = hash_password(otp)
    user.otp_expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    user.otp_sent_at = now
    await db.commit()
    await send_verification_code(user.email, otp)
    return {"message": "Код отправлен"}
