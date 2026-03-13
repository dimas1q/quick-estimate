from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership
from app.utils.auth import get_current_admin, get_current_user, hash_password, verify_password
from app.schemas.user import UserUpdate, PasswordUpdate
from app.schemas.user import (
    AdminActivationUpdate,
    AdminRoleUpdate,
    ApproverUserOut,
    WorkspaceMembershipOut,
    WorkspaceSwitchIn,
    UserOut,
)
from app.schemas.paginated import Paginated

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("/me/workspaces", response_model=list[WorkspaceMembershipOut])
async def list_my_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(OrganizationMembership.user_id == current_user.id)
        .order_by(Organization.name.asc())
    )
    rows = result.all()

    workspaces = [
        WorkspaceMembershipOut(
            organization_id=organization.id,
            organization_name=organization.name,
            organization_slug=organization.slug,
            organization_domain=organization.domain,
            role=membership.role,
            is_current=organization.id == current_user.current_organization_id,
        )
        for membership, organization in rows
    ]
    workspaces.sort(
        key=lambda workspace: (
            0 if workspace.is_current else 1,
            workspace.organization_name.lower(),
        )
    )
    return workspaces


@router.post("/me/workspaces/switch", response_model=UserOut)
async def switch_current_workspace(
    payload: WorkspaceSwitchIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.current_organization_id == payload.organization_id:
        return current_user

    membership_result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.organization_id == payload.organization_id,
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Нет доступа к выбранному рабочему пространству",
        )

    current_user.current_organization_id = payload.organization_id
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/approvers", response_model=list[ApproverUserOut])
async def list_approvers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.current_organization_id is None:
        return [current_user]

    result = await db.execute(
        select(User)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == current_user.current_organization_id,
            User.is_active.is_(True),
        )
        .order_by(User.name.asc(), User.login.asc())
    )
    return result.scalars().all()


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


@router.get("/admin/users", response_model=Paginated[UserOut])
async def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total = await db.scalar(select(func.count()).select_from(User))
    result = await db.execute(
        select(User).order_by(User.id.asc()).offset((page - 1) * limit).limit(limit)
    )
    return {"items": result.scalars().all(), "total": total}


@router.patch("/admin/users/{user_id}/role", response_model=UserOut)
async def admin_update_user_role(
    user_id: int,
    data: AdminRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if current_admin.id == user_id and not data.is_admin:
        raise HTTPException(
            status_code=400, detail="Нельзя снять роль администратора у самого себя"
        )

    target_user.is_admin = data.is_admin
    await db.commit()
    await db.refresh(target_user)
    return target_user


@router.patch("/admin/users/{user_id}/activation", response_model=UserOut)
async def admin_update_user_activation(
    user_id: int,
    data: AdminActivationUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if current_admin.id == user_id and not data.is_active:
        raise HTTPException(status_code=400, detail="Нельзя деактивировать самого себя")

    target_user.is_active = data.is_active
    await db.commit()
    await db.refresh(target_user)
    return target_user
