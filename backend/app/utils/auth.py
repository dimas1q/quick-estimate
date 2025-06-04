# utils/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.secret_key import load_or_create_secret_key
from sqlalchemy.future import select
from sqlalchemy import or_
from app.core.database import get_db
from app.models.user import User
import bcrypt

# Конфигурация
SECRET_KEY = load_or_create_secret_key("config/secret.key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# 🔒 Хэширование пароля
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# 🔑 Проверка пользователя по email или логину
async def authenticate_user(
    db: AsyncSession, identifier: str, password: str
) -> Optional[User]:
    stmt = select(User).where(or_(User.email == identifier, User.login == identifier))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return None

    return user


# 🔐 Токен
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# 👤 Текущий пользователь
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if str(sub).isdigit():
        result = await db.execute(select(User).where(User.id == int(sub)))
    else:
        # Backward compatibility for tokens containing email
        result = await db.execute(select(User).where(User.email == str(sub)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# 👑 Проверка прав администратора
async def get_current_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return user
