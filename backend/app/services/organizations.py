import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User


PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "mail.ru",
    "yandex.ru",
    "yandex.com",
    "proton.me",
    "protonmail.com",
    "aol.com",
    "zoho.com",
}


def _extract_email_domain(email: str) -> str | None:
    if "@" not in email:
        return None
    return email.rsplit("@", 1)[-1].strip().lower() or None


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
    domain = _extract_email_domain(email)
    company_name = (company or "").strip() or None

    if (
        settings.ORGANIZATIONS_AUTO_DOMAIN_ENABLED
        and domain
        and domain not in PUBLIC_EMAIL_DOMAINS
    ):
        existing_result = await db.execute(
            select(Organization).where(Organization.domain == domain)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return existing, "member"

        org_name = company_name or f"Команда {domain}"
        org_slug = await _ensure_unique_organization_slug(db, domain.replace(".", "-"))
        organization = Organization(name=org_name[:120], slug=org_slug, domain=domain)
        db.add(organization)
        await db.flush()
        return organization, "owner"

    workspace_name = company_name or f"Рабочее пространство {login}"
    org_slug = await _ensure_unique_organization_slug(db, f"ws-{login}")
    organization = Organization(name=workspace_name[:120], slug=org_slug, domain=None)
    db.add(organization)
    await db.flush()
    return organization, "owner"


def ensure_user_in_workspace(
    db: AsyncSession,
    *,
    user: User,
    organization: Organization,
    role: str,
) -> None:
    db.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role=role,
        )
    )
    user.current_organization_id = organization.id
