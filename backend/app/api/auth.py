# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.utils.auth import authenticate_user, get_current_user
from app.utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(tags=["auth"])


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

    new_user = User(
        login=user.login,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    identifier = form_data.username
    password = form_data.password

    db_user = await authenticate_user(db, identifier, password)

    if not db_user:
        raise HTTPException(status_code=401, detail="Неверный логин/email или пароль")

    token = create_access_token(data={"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user
