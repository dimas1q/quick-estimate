# api/auth.py
from datetime import datetime, timedelta, timezone
import asyncio
import json
import re
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.user import (
    EmailRequest,
    GoogleOAuthRequest,
    RefreshTokenRequest,
    UserCreate,
    UserOut,
    VerifyCode,
)
from app.utils.auth import authenticate_user
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_password,
    verify_password,
)
from app.utils.otp import generate_code
from app.utils.email import send_verification_code

router = APIRouter(tags=["auth"])
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _google_client_id() -> str:
    return settings.GOOGLE_OAUTH_CLIENT_ID.strip()


def _build_login_candidate(email: str) -> str:
    base = email.split("@", 1)[0].lower()
    normalized = re.sub(r"[^a-z0-9_.-]", "_", base).strip("._-")
    if not normalized:
        normalized = "user"
    if len(normalized) < 3:
        normalized = f"{normalized}_user"
    return normalized[:48]


async def _ensure_unique_login(db: AsyncSession, email: str) -> str:
    base_login = _build_login_candidate(email)
    for suffix in range(0, 10000):
        candidate = base_login if suffix == 0 else f"{base_login}_{suffix}"
        result = await db.execute(select(User).where(User.login == candidate))
        existing = result.scalar_one_or_none()
        if not existing:
            return candidate
    raise HTTPException(status_code=500, detail="Не удалось подобрать уникальный логин")


def _verify_google_token(credential: str, allowed_client_id: str) -> dict:
    if not credential:
        raise HTTPException(status_code=400, detail="Пустой OAuth credential")

    try:
        query = urlencode({"id_token": credential})
        with urlopen(f"https://oauth2.googleapis.com/tokeninfo?{query}", timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Неверный Google токен")

    issuer = payload.get("iss")
    audience = payload.get("aud")
    email = payload.get("email")
    email_verified = payload.get("email_verified")

    if issuer not in GOOGLE_ISSUERS:
        raise HTTPException(status_code=401, detail="Неверный издатель Google токена")
    if audience != allowed_client_id:
        raise HTTPException(status_code=401, detail="Google токен выдан для другого клиента")
    if not email or email_verified not in {True, "true", "True"}:
        raise HTTPException(status_code=401, detail="Google аккаунт не подтвержден")

    return payload


async def _find_user_by_identifier(db: AsyncSession, identifier: str) -> User | None:
    result = await db.execute(
        select(User).where(or_(User.email == identifier, User.login == identifier))
    )
    return result.scalar_one_or_none()


def _lock_retry_after_seconds(locked_until: datetime, now: datetime) -> int:
    return max(1, int((locked_until - now).total_seconds()))


def _issue_tokens(user_id: int) -> dict[str, str]:
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def _register_failed_login(db: AsyncSession, user: User, now: datetime) -> bool:
    attempts = int(user.failed_login_attempts or 0) + 1
    if attempts >= settings.AUTH_MAX_FAILED_LOGIN_ATTEMPTS:
        user.failed_login_attempts = 0
        user.locked_until = now + timedelta(minutes=settings.AUTH_LOCK_MINUTES)
        await db.commit()
        return True

    user.failed_login_attempts = attempts
    user.locked_until = None
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
    try:
        await send_verification_code(user.email, otp)
    except RuntimeError:
        await db.delete(new_user)
        await db.commit()
        raise HTTPException(status_code=502, detail="Не удалось отправить код подтверждения")
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

    if db_user and db_user.locked_until:
        if db_user.locked_until > now:
            retry_after = _lock_retry_after_seconds(db_user.locked_until, now)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Слишком много попыток входа. Повторите позже.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        db_user.locked_until = None

    authed_user = await authenticate_user(db, identifier, password)
    if not authed_user:
        if db_user:
            locked_now = await _register_failed_login(db, db_user, now)
            if locked_now and db_user.locked_until:
                retry_after = _lock_retry_after_seconds(db_user.locked_until, now)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Слишком много попыток входа. Повторите позже.",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        raise HTTPException(status_code=401, detail="Неверный логин/email или пароль")

    await _clear_login_locks_if_needed(db, authed_user)
    if not authed_user.is_active:
        return JSONResponse(status_code=403, content={"verify_required": True, "email": authed_user.email})

    return _issue_tokens(authed_user.id)


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

    return _issue_tokens(user.id)


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
    try:
        await send_verification_code(user.email, otp)
    except RuntimeError:
        await db.rollback()
        raise HTTPException(status_code=502, detail="Не удалось отправить код подтверждения")
    await db.commit()
    return {"message": "Код отправлен"}


@router.post("/oauth/google")
async def google_oauth_login(
    data: GoogleOAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    allowed_client_id = _google_client_id()
    if not allowed_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth не настроен")

    google_payload = await asyncio.to_thread(
        _verify_google_token, data.credential, allowed_client_id
    )
    email = str(google_payload["email"]).lower()
    user_name = google_payload.get("name")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        generated_password = secrets.token_urlsafe(32)
        login = await _ensure_unique_login(db, email)
        user = User(
            login=login,
            email=email,
            name=user_name,
            hashed_password=hash_password(generated_password),
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        changed = False
        if not user.is_active:
            user.is_active = True
            changed = True
        if (user.failed_login_attempts or 0) != 0:
            user.failed_login_attempts = 0
            changed = True
        if user.locked_until is not None:
            user.locked_until = None
            changed = True
        if not user.name and user_name:
            user.name = user_name
            changed = True
        if changed:
            await db.commit()
            await db.refresh(user)

    return _issue_tokens(user.id)


@router.post("/refresh")
async def refresh_tokens(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Невалидный refresh token")
    try:
        payload = decode_jwt_token(data.refresh_token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise credentials_exception

    sub = payload.get("sub")
    if not sub:
        raise credentials_exception

    if str(sub).isdigit():
        result = await db.execute(select(User).where(User.id == int(sub)))
    else:
        result = await db.execute(select(User).where(User.email == str(sub)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exception

    return _issue_tokens(user.id)
