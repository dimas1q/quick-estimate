import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import (
    Organization,
    OrganizationMembership,
    WORKSPACE_ROLE_OWNER,
)
from app.models.user import User


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:100] if normalized else "workspace"


async def _ensure_unique_organization_slug(
    db: AsyncSession, base_slug: str
) -> str:
    base = _slugify(base_slug)
    for idx in range(0, 10000):
        slug = base if idx == 0 else f"{base}-{idx}"
        result = await db.execute(select(Organization.id).where(Organization.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
    raise RuntimeError("Не удалось сгенерировать уникальный slug workspace")


async def resolve_workspace_for_new_user(
    db: AsyncSession,
    *,
    email: str,
    login: str,
    company: str | None = None,
) -> tuple[Organization, str]:
    company_name = (company or "").strip() or None

    workspace_name = company_name or f"Рабочее пространство {login}"
    org_slug = await _ensure_unique_organization_slug(db, f"ws-{login}")
    organization = Organization(name=workspace_name[:120], slug=org_slug, domain=None)
    db.add(organization)
    flush = getattr(db, "flush", None)
    if callable(flush):
        await flush()
    return organization, WORKSPACE_ROLE_OWNER


def ensure_user_in_workspace(
    db: AsyncSession,
    *,
    user: User,
    organization: Organization,
    role: str,
    set_default_if_missing: bool = False,
) -> None:
    db.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role=role,
        )
    )
    user.current_organization_id = organization.id
    if set_default_if_missing and user.default_organization_id is None:
        user.default_organization_id = organization.id
