from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user, hash_password, verify_password
from app.schemas.user import UserUpdate, PasswordUpdate
from app.schemas.user import UserCreate, UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me")
async def update_user(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # проверка email
    if data.email != current_user.email:
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email уже используется")

    # проверка login
    if data.login != current_user.login:
        result = await db.execute(select(User).where(User.login == data.login))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Логин уже используется")

    current_user.login = data.login
    current_user.email = data.email
    current_user.name = data.name
    current_user.company = data.company

    await db.commit()
    return {"message": "Профиль обновлён"}


@router.put("/me/password")
async def change_password(
    data: PasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Новые пароли не совпадают")

    current_user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"message": "Пароль обновлён"}
