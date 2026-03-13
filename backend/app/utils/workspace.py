from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.organization import (
    OrganizationMembership,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_APPROVER,
    WORKSPACE_ROLE_ESTIMATOR,
    WORKSPACE_ROLE_GUEST,
    WORKSPACE_ROLE_OWNER,
)
from app.models.user import User
from app.utils.auth import get_current_user

WORKSPACE_PERMISSION_VIEW = "workspace:view"
WORKSPACE_PERMISSION_DATA_VIEW = "data:view"
WORKSPACE_PERMISSION_DATA_EDIT = "data:edit"
WORKSPACE_PERMISSION_APPROVAL_MANAGE = "approval:manage"
WORKSPACE_PERMISSION_APPROVAL_SIGN = "approval:sign"
WORKSPACE_PERMISSION_MEMBERS_MANAGE = "members:manage"
WORKSPACE_PERMISSION_INVITES_MANAGE = "invites:manage"
WORKSPACE_PERMISSION_OWNER_TRANSFER = "owner:transfer"
WORKSPACE_PERMISSION_WORKSPACE_DELETE = "workspace:delete"

ROLE_PERMISSIONS = {
    WORKSPACE_ROLE_OWNER: {
        WORKSPACE_PERMISSION_VIEW,
        WORKSPACE_PERMISSION_DATA_VIEW,
        WORKSPACE_PERMISSION_DATA_EDIT,
        WORKSPACE_PERMISSION_APPROVAL_MANAGE,
        WORKSPACE_PERMISSION_APPROVAL_SIGN,
        WORKSPACE_PERMISSION_MEMBERS_MANAGE,
        WORKSPACE_PERMISSION_INVITES_MANAGE,
        WORKSPACE_PERMISSION_OWNER_TRANSFER,
        WORKSPACE_PERMISSION_WORKSPACE_DELETE,
    },
    WORKSPACE_ROLE_ADMIN: {
        WORKSPACE_PERMISSION_VIEW,
        WORKSPACE_PERMISSION_DATA_VIEW,
        WORKSPACE_PERMISSION_DATA_EDIT,
        WORKSPACE_PERMISSION_APPROVAL_MANAGE,
        WORKSPACE_PERMISSION_APPROVAL_SIGN,
        WORKSPACE_PERMISSION_MEMBERS_MANAGE,
        WORKSPACE_PERMISSION_INVITES_MANAGE,
    },
    WORKSPACE_ROLE_APPROVER: {
        WORKSPACE_PERMISSION_VIEW,
        WORKSPACE_PERMISSION_DATA_VIEW,
        WORKSPACE_PERMISSION_DATA_EDIT,
        WORKSPACE_PERMISSION_APPROVAL_SIGN,
    },
    WORKSPACE_ROLE_ESTIMATOR: {
        WORKSPACE_PERMISSION_VIEW,
        WORKSPACE_PERMISSION_DATA_VIEW,
        WORKSPACE_PERMISSION_DATA_EDIT,
    },
    WORKSPACE_ROLE_GUEST: {
        WORKSPACE_PERMISSION_VIEW,
        WORKSPACE_PERMISSION_DATA_VIEW,
    },
}


@dataclass(slots=True)
class WorkspaceContext:
    user: User
    organization_id: int
    role: str


def has_workspace_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


async def get_workspace_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceContext:
    if current_user.current_organization_id is None:
        raise HTTPException(
            status_code=409,
            detail="Вы не привязаны к рабочему пространству",
        )

    membership_result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.organization_id == current_user.current_organization_id,
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership:
        # Current workspace pointer is stale (membership was removed or workspace deleted).
        # Normalize user state so UI can explicitly request workspace selection.
        if current_user.current_organization_id is not None:
            current_user.current_organization_id = None
            await db.commit()
        raise HTTPException(
            status_code=409,
            detail="Текущее рабочее пространство не выбрано",
        )

    return WorkspaceContext(
        user=current_user,
        organization_id=int(current_user.current_organization_id),
        role=(membership.role or WORKSPACE_ROLE_GUEST).lower(),
    )


def require_workspace_permission(permission: str) -> Callable:
    async def _dependency(
        context: WorkspaceContext = Depends(get_workspace_context),
    ) -> WorkspaceContext:
        if not has_workspace_permission(context.role, permission):
            raise HTTPException(
                status_code=403,
                detail="Недостаточно прав для выполнения действия",
            )
        return context

    return _dependency
