from datetime import datetime, timedelta, timezone
import hashlib
import logging
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.organization import (
    Organization,
    OrganizationMembership,
    WORKSPACE_INVITE_STATUSES,
    WORKSPACE_INVITE_STATUS_ACCEPTED,
    WORKSPACE_INVITE_STATUS_EXPIRED,
    WORKSPACE_INVITE_STATUS_PENDING,
    WORKSPACE_INVITE_STATUS_REVOKED,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_APPROVER,
    WORKSPACE_ROLE_ESTIMATOR,
    WORKSPACE_ROLE_GUEST,
    WORKSPACE_ROLE_OWNER,
    WORKSPACE_ROLES,
    WorkspaceInvitation,
)
from app.models.user import User
from app.schemas.workspace import (
    IncomingWorkspaceInviteOut,
    WorkspaceCreateIn,
    WorkspaceCurrentOut,
    WorkspaceDeleteIn,
    WorkspaceInviteCreateIn,
    WorkspaceInviteCreateOut,
    WorkspaceInviteOut,
    WorkspaceMemberOut,
    WorkspaceMemberRoleUpdateIn,
    WorkspaceOwnerTransferIn,
    WorkspaceUpdateIn,
)
from app.utils.email import send_email
from app.utils.auth import get_current_user
from app.utils.workspace import (
    WORKSPACE_PERMISSION_INVITES_MANAGE,
    WORKSPACE_PERMISSION_MEMBERS_MANAGE,
    WORKSPACE_PERMISSION_OWNER_TRANSFER,
    WORKSPACE_PERMISSION_VIEW,
    WORKSPACE_PERMISSION_WORKSPACE_DELETE,
    WorkspaceContext,
    get_workspace_context,
    require_workspace_permission,
)

router = APIRouter(tags=["workspaces"], dependencies=[Depends(get_current_user)])
logger = logging.getLogger(__name__)

ALLOWED_ASSIGNABLE_ROLES = {
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_ESTIMATOR,
    WORKSPACE_ROLE_GUEST,
    WORKSPACE_ROLE_APPROVER,
}


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:100] if normalized else "workspace"


async def _ensure_unique_workspace_slug(db: AsyncSession, base_slug: str) -> str:
    base = _slugify(base_slug)
    for idx in range(0, 10000):
        slug = base if idx == 0 else f"{base}-{idx}"
        existing = await db.scalar(select(Organization.id).where(Organization.slug == slug))
        if existing is None:
            return slug
    raise HTTPException(status_code=500, detail="Не удалось сгенерировать slug рабочего пространства")


def _normalize_role(raw_role: str) -> str:
    role = (raw_role or "").strip().lower()
    if role not in WORKSPACE_ROLES:
        raise HTTPException(status_code=422, detail="Недопустимая роль рабочего пространства")
    return role


def _normalize_domain(raw_domain: str | None) -> str | None:
    if raw_domain is None:
        return None
    candidate = raw_domain.strip().lower()
    if not candidate:
        return None
    if "@" in candidate:
        raise HTTPException(status_code=422, detail="Домен должен быть в формате company.com")
    candidate = re.sub(r"^https?://", "", candidate).strip("/")
    if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", candidate):
        raise HTTPException(status_code=422, detail="Некорректный домен рабочего пространства")
    return candidate


def _to_invite_out(invitation: WorkspaceInvitation) -> WorkspaceInviteOut:
    return WorkspaceInviteOut(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
        invited_by_user_id=invitation.invited_by_user_id,
        created_at=invitation.created_at,
    )


@router.post("/", response_model=WorkspaceCurrentOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    name = payload.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Название рабочего пространства слишком короткое")

    domain = _normalize_domain(payload.domain)
    if domain:
        domain_in_use = await db.scalar(
            select(func.count()).select_from(Organization).where(Organization.domain == domain)
        )
        if domain_in_use:
            raise HTTPException(status_code=409, detail="Такой домен уже используется другим workspace")

    slug = await _ensure_unique_workspace_slug(db, name)
    organization = Organization(name=name, slug=slug, domain=domain)
    db.add(organization)
    await db.flush()

    db.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role=WORKSPACE_ROLE_OWNER,
        )
    )
    user.current_organization_id = organization.id
    if user.default_organization_id is None:
        user.default_organization_id = organization.id
    await db.commit()
    await db.refresh(organization)

    return WorkspaceCurrentOut(
        organization_id=organization.id,
        name=organization.name,
        slug=organization.slug,
        domain=organization.domain,
        role=WORKSPACE_ROLE_OWNER,
        is_default=user.default_organization_id == organization.id,
    )


@router.get("/current", response_model=WorkspaceCurrentOut)
async def get_current_workspace(
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(get_workspace_context),
):
    organization = await db.get(Organization, context.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")
    return WorkspaceCurrentOut(
        organization_id=organization.id,
        name=organization.name,
        slug=organization.slug,
        domain=organization.domain,
        role=context.role,
        is_default=context.user.default_organization_id == organization.id,
    )


@router.patch("/current", response_model=WorkspaceCurrentOut)
async def update_current_workspace(
    payload: WorkspaceUpdateIn,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_MEMBERS_MANAGE)
    ),
):
    organization = await db.get(Organization, context.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        new_name = (update_data.get("name") or "").strip()
        if len(new_name) < 2:
            raise HTTPException(status_code=422, detail="Название рабочего пространства слишком короткое")
        if new_name != organization.name:
            organization.name = new_name

    if "domain" in update_data:
        new_domain = _normalize_domain(update_data.get("domain"))
        if new_domain != organization.domain:
            if new_domain:
                domain_in_use = await db.scalar(
                    select(func.count())
                    .select_from(Organization)
                    .where(
                        Organization.domain == new_domain,
                        Organization.id != organization.id,
                    )
                )
                if domain_in_use:
                    raise HTTPException(
                        status_code=409,
                        detail="Такой домен уже используется другим workspace",
                    )
            organization.domain = new_domain

    await db.commit()
    await db.refresh(organization)
    return WorkspaceCurrentOut(
        organization_id=organization.id,
        name=organization.name,
        slug=organization.slug,
        domain=organization.domain,
        role=context.role,
        is_default=context.user.default_organization_id == organization.id,
    )


@router.get("/current/members", response_model=list[WorkspaceMemberOut])
async def list_workspace_members(
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_VIEW)
    ),
):
    result = await db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(OrganizationMembership.organization_id == context.organization_id)
        .order_by(User.name.asc(), User.login.asc())
    )
    rows = result.all()
    return [
        WorkspaceMemberOut(
            user_id=user.id,
            login=user.login,
            email=user.email,
            name=user.name,
            company=user.company,
            role=membership.role,
            is_active=bool(user.is_active),
            joined_at=membership.created_at,
            is_current_user=user.id == context.user.id,
        )
        for membership, user in rows
    ]


@router.patch("/current/members/{user_id}/role", response_model=WorkspaceMemberOut)
async def update_workspace_member_role(
    user_id: int,
    payload: WorkspaceMemberRoleUpdateIn,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_MEMBERS_MANAGE)
    ),
):
    role = _normalize_role(payload.role)
    if role == WORKSPACE_ROLE_OWNER:
        raise HTTPException(
            status_code=422,
            detail="Роль владельца передается только через отдельную операцию",
        )
    if role not in ALLOWED_ASSIGNABLE_ROLES:
        raise HTTPException(status_code=422, detail="Недопустимая роль для назначения")

    membership_result = await db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.user_id == user_id,
        )
    )
    row = membership_result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Участник не найден")
    membership, user = row

    if membership.role == WORKSPACE_ROLE_OWNER:
        raise HTTPException(
            status_code=409,
            detail="Нельзя менять роль владельца через этот endpoint",
        )
    if context.role == WORKSPACE_ROLE_ADMIN and membership.role == WORKSPACE_ROLE_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Администратор не может менять роль другого администратора",
        )

    membership.role = role
    await db.commit()
    await db.refresh(membership)
    return WorkspaceMemberOut(
        user_id=user.id,
        login=user.login,
        email=user.email,
        name=user.name,
        company=user.company,
        role=membership.role,
        is_active=bool(user.is_active),
        joined_at=membership.created_at,
        is_current_user=user.id == context.user.id,
    )


@router.delete("/current/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_MEMBERS_MANAGE)
    ),
):
    if user_id == context.user.id:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить самого себя из текущего рабочего пространства",
        )

    membership_result = await db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.user_id == user_id,
        )
    )
    row = membership_result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Участник не найден")
    membership, target_user = row
    if membership.role == WORKSPACE_ROLE_OWNER:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить владельца рабочего пространства",
        )
    if target_user.default_organization_id == context.organization_id:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить пользователя из его дефолтного рабочего пространства",
        )
    if context.role == WORKSPACE_ROLE_ADMIN and membership.role == WORKSPACE_ROLE_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Администратор не может удалить другого администратора",
        )

    await db.delete(membership)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/current/transfer-ownership", response_model=WorkspaceCurrentOut)
async def transfer_workspace_ownership(
    payload: WorkspaceOwnerTransferIn,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_OWNER_TRANSFER)
    ),
):
    if payload.new_owner_user_id == context.user.id:
        raise HTTPException(status_code=409, detail="Пользователь уже является владельцем")

    current_owner_result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.role == WORKSPACE_ROLE_OWNER,
        )
    )
    current_owner = current_owner_result.scalar_one_or_none()
    if not current_owner or current_owner.user_id != context.user.id:
        raise HTTPException(status_code=403, detail="Передача владельца доступна только текущему владельцу")

    new_owner_result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.user_id == payload.new_owner_user_id,
        )
    )
    new_owner = new_owner_result.scalar_one_or_none()
    if not new_owner:
        raise HTTPException(status_code=404, detail="Новый владелец должен быть участником рабочего пространства")

    current_owner.role = WORKSPACE_ROLE_ADMIN
    new_owner.role = WORKSPACE_ROLE_OWNER
    await db.commit()

    organization = await db.get(Organization, context.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")

    return WorkspaceCurrentOut(
        organization_id=organization.id,
        name=organization.name,
        slug=organization.slug,
        domain=organization.domain,
        role=WORKSPACE_ROLE_ADMIN,
        is_default=context.user.default_organization_id == organization.id,
    )


@router.delete("/current", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    payload: WorkspaceDeleteIn,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_WORKSPACE_DELETE)
    ),
):
    organization = await db.get(Organization, context.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")
    if context.user.default_organization_id == organization.id:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить Стандартное рабочее пространство, привязанное к аккаунту",
        )

    default_links_count = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.default_organization_id == organization.id)
    )
    if default_links_count:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить рабочее пространство: оно является дефолтным для одного или нескольких аккаунтов",
        )

    if payload.confirm_name.strip() != organization.name:
        raise HTTPException(status_code=422, detail="Название рабочего пространства введено неверно")

    await db.delete(organization)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/current/invitations", response_model=list[WorkspaceInviteOut])
async def list_workspace_invitations(
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_INVITES_MANAGE)
    ),
):
    result = await db.execute(
        select(WorkspaceInvitation)
        .where(WorkspaceInvitation.organization_id == context.organization_id)
        .order_by(WorkspaceInvitation.created_at.desc())
    )
    return [_to_invite_out(invitation) for invitation in result.scalars().all()]


@router.post("/current/invitations", response_model=WorkspaceInviteCreateOut, status_code=201)
async def create_workspace_invitation(
    payload: WorkspaceInviteCreateIn,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_INVITES_MANAGE)
    ),
):
    role = _normalize_role(payload.role)
    if role == WORKSPACE_ROLE_OWNER:
        raise HTTPException(status_code=422, detail="Приглашать с ролью владельца нельзя")

    email = payload.email.strip().lower()
    membership_exists = await db.scalar(
        select(func.count())
        .select_from(OrganizationMembership)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(
            OrganizationMembership.organization_id == context.organization_id,
            User.email == email,
        )
    )
    if membership_exists:
        raise HTTPException(status_code=409, detail="Пользователь уже состоит в рабочем пространстве")

    pending_invites_result = await db.execute(
        select(WorkspaceInvitation).where(
            WorkspaceInvitation.organization_id == context.organization_id,
            WorkspaceInvitation.email == email,
            WorkspaceInvitation.status == WORKSPACE_INVITE_STATUS_PENDING,
        )
    )
    for invite in pending_invites_result.scalars().all():
        invite.status = WORKSPACE_INVITE_STATUS_REVOKED

    token_hash = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
    invitation = WorkspaceInvitation(
        organization_id=context.organization_id,
        email=email,
        role=role,
        token_hash=token_hash,
        status=WORKSPACE_INVITE_STATUS_PENDING,
        invited_by_user_id=context.user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    organization = await db.get(Organization, context.organization_id)
    email_sent = False
    if organization:
        app_url = settings.APP_DOMAIN.strip() if settings.APP_DOMAIN else ""
        open_link = f"{app_url}/workspace/settings" if app_url else "в разделе Настройки пространства"
        subject = f"Приглашение в рабочее пространство «{organization.name}»"
        body = (
            f"Здравствуйте!\n\n"
            f"Пользователь {context.user.login} пригласил вас в рабочее пространство "
            f"«{organization.name}» в роли «{role}».\n"
            f"Срок действия приглашения: до {invitation.expires_at.astimezone().strftime('%d.%m.%Y %H:%M')}.\n\n"
            f"Откройте приглашения в приложении: {open_link}\n"
            f"После входа перейдите в раздел «Настройки пространства» и примите или отклоните приглашение."
        )
        try:
            await send_email(
                subject=subject,
                body=body,
                to=email,
            )
            email_sent = True
        except RuntimeError:
            logger.warning(
                "Не удалось отправить email приглашение в workspace %s для %s",
                context.organization_id,
                email,
            )

    return WorkspaceInviteCreateOut(
        invitation=_to_invite_out(invitation),
        email_sent=email_sent,
    )


@router.delete("/current/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_workspace_invitation(
    invitation_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_INVITES_MANAGE)
    ),
):
    invitation = await db.get(WorkspaceInvitation, invitation_id)
    if not invitation or invitation.organization_id != context.organization_id:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")

    if invitation.status != WORKSPACE_INVITE_STATUS_PENDING:
        raise HTTPException(status_code=409, detail="Приглашение уже обработано")

    invitation.status = WORKSPACE_INVITE_STATUS_REVOKED
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/invitations/incoming", response_model=list[IncomingWorkspaceInviteOut])
async def list_incoming_workspace_invitations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    normalized_email = user.email.strip().lower()
    result = await db.execute(
        select(WorkspaceInvitation, Organization, User)
        .join(Organization, Organization.id == WorkspaceInvitation.organization_id)
        .outerjoin(User, User.id == WorkspaceInvitation.invited_by_user_id)
        .where(
            WorkspaceInvitation.email == normalized_email,
            WorkspaceInvitation.status == WORKSPACE_INVITE_STATUS_PENDING,
        )
        .order_by(WorkspaceInvitation.created_at.desc())
    )
    rows = result.all()
    now = datetime.now(timezone.utc)
    incoming: list[IncomingWorkspaceInviteOut] = []
    for invitation, organization, inviter in rows:
        if invitation.expires_at <= now:
            invitation.status = WORKSPACE_INVITE_STATUS_EXPIRED
            continue
        incoming.append(
            IncomingWorkspaceInviteOut(
                id=invitation.id,
                organization_id=organization.id,
                organization_name=organization.name,
                organization_slug=organization.slug,
                organization_domain=organization.domain,
                role=invitation.role,
                status=invitation.status,
                invited_by_user_id=invitation.invited_by_user_id,
                invited_by_login=inviter.login if inviter else None,
                invited_by_email=inviter.email if inviter else None,
                expires_at=invitation.expires_at,
                created_at=invitation.created_at,
            )
        )
    await db.commit()
    return incoming


async def _accept_invitation(
    *,
    db: AsyncSession,
    invitation: WorkspaceInvitation,
    user: User,
):
    now = datetime.now(timezone.utc)
    if invitation.expires_at <= now:
        invitation.status = WORKSPACE_INVITE_STATUS_EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="Срок действия приглашения истек")

    if user.email.strip().lower() != invitation.email.strip().lower():
        raise HTTPException(status_code=403, detail="Это приглашение предназначено для другого email")

    membership = await db.scalar(
        select(func.count())
        .select_from(OrganizationMembership)
        .where(
            OrganizationMembership.organization_id == invitation.organization_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if not membership:
        db.add(
            OrganizationMembership(
                organization_id=invitation.organization_id,
                user_id=user.id,
                role=invitation.role,
            )
        )

    invitation.status = WORKSPACE_INVITE_STATUS_ACCEPTED
    invitation.accepted_by_user_id = user.id
    user.current_organization_id = invitation.organization_id
    await db.commit()
    return {"detail": "Приглашение принято", "organization_id": invitation.organization_id}


@router.post("/invitations/{invitation_id}/accept")
async def accept_workspace_invitation_by_id(
    invitation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    invitation = await db.get(WorkspaceInvitation, invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    if invitation.status not in WORKSPACE_INVITE_STATUSES:
        raise HTTPException(status_code=409, detail="Некорректный статус приглашения")
    if invitation.status != WORKSPACE_INVITE_STATUS_PENDING:
        raise HTTPException(status_code=409, detail="Приглашение уже обработано")

    return await _accept_invitation(db=db, invitation=invitation, user=user)


@router.post("/invitations/{invitation_id}/reject")
async def reject_workspace_invitation_by_id(
    invitation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    invitation = await db.get(WorkspaceInvitation, invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")
    if invitation.status not in WORKSPACE_INVITE_STATUSES:
        raise HTTPException(status_code=409, detail="Некорректный статус приглашения")
    if invitation.status != WORKSPACE_INVITE_STATUS_PENDING:
        raise HTTPException(status_code=409, detail="Приглашение уже обработано")
    if user.email.strip().lower() != invitation.email.strip().lower():
        raise HTTPException(status_code=403, detail="Это приглашение предназначено для другого email")

    invitation.status = WORKSPACE_INVITE_STATUS_REVOKED
    invitation.accepted_by_user_id = user.id
    await db.commit()
    return {"detail": "Приглашение отклонено"}
