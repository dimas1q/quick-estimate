"""seed development data only

Revision ID: d1e2f3a4b5c6
Revises: f0e1d2c3b4a5
Create Date: 2026-03-11 23:50:00
"""

from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "f0e1d2c3b4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEV_LOGIN = "dev_demo"
DEV_EMAIL = "dev_demo@example.com"
DEV_PASSWORD = "devpassword"


def _is_development() -> bool:
    env_name = (os.getenv("APP_ENV") or os.getenv("ENV") or "").lower()
    return env_name in {"dev", "development", "local"}


def _get_or_create_user(conn) -> int:
    existing_user_id = conn.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": DEV_EMAIL},
    ).scalar()
    if existing_user_id:
        return int(existing_user_id)

    import bcrypt

    password_hash = bcrypt.hashpw(DEV_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user_id = conn.execute(
        sa.text(
            """
            INSERT INTO users (email, login, name, company, hashed_password, is_admin, is_active)
            VALUES (:email, :login, :name, :company, :hashed_password, false, true)
            RETURNING id
            """
        ),
        {
            "email": DEV_EMAIL,
            "login": DEV_LOGIN,
            "name": "Development User",
            "company": "QuickEstimate Dev",
            "hashed_password": password_hash,
        },
    ).scalar_one()
    return int(user_id)


def _get_or_create_client(conn, user_id: int) -> int:
    existing_client_id = conn.execute(
        sa.text(
            """
            SELECT id
            FROM clients
            WHERE user_id = :user_id AND name = :name
            """
        ),
        {"user_id": user_id, "name": "Dev Client"},
    ).scalar()
    if existing_client_id:
        return int(existing_client_id)

    client_id = conn.execute(
        sa.text(
            """
            INSERT INTO clients (name, company, email, phone, user_id)
            VALUES (:name, :company, :email, :phone, :user_id)
            RETURNING id
            """
        ),
        {
            "name": "Dev Client",
            "company": "Client QA LLC",
            "email": "qa.client@example.com",
            "phone": "+1-555-0101",
            "user_id": user_id,
        },
    ).scalar_one()
    return int(client_id)


def _get_or_create_template(conn, user_id: int) -> int:
    existing_template_id = conn.execute(
        sa.text(
            """
            SELECT id
            FROM estimate_templates
            WHERE user_id = :user_id AND name = :name
            """
        ),
        {"user_id": user_id, "name": "Dev Event Template"},
    ).scalar()
    if existing_template_id:
        return int(existing_template_id)

    template_id = conn.execute(
        sa.text(
            """
            INSERT INTO estimate_templates (name, description, use_internal_price, user_id)
            VALUES (:name, :description, true, :user_id)
            RETURNING id
            """
        ),
        {
            "name": "Dev Event Template",
            "description": "Template with sample service positions for development.",
            "user_id": user_id,
        },
    ).scalar_one()

    conn.execute(
        sa.text(
            """
            INSERT INTO estimate_items
                (name, description, quantity, unit, internal_price, external_price, category, template_id)
            VALUES
                ('Stage Setup', 'Assembling stage equipment', 1, 'проект', 25000, 42000, 'Сцена', :template_id),
                ('Light Package', 'Basic lighting package', 8, 'час', 3500, 6000, 'Свет', :template_id)
            """
        ),
        {"template_id": int(template_id)},
    )
    return int(template_id)


def _get_or_create_estimate(conn, user_id: int, client_id: int) -> int:
    existing_estimate_id = conn.execute(
        sa.text(
            """
            SELECT id
            FROM estimates
            WHERE user_id = :user_id AND name = :name
            """
        ),
        {"user_id": user_id, "name": "Dev Seed Estimate"},
    ).scalar()
    if existing_estimate_id:
        return int(existing_estimate_id)

    estimate_id = conn.execute(
        sa.text(
            """
            INSERT INTO estimates
                (name, user_id, client_id, responsible, status, vat_enabled, vat_rate, use_internal_price)
            VALUES
                (:name, :user_id, :client_id, :responsible, 'draft', true, 20, true)
            RETURNING id
            """
        ),
        {
            "name": "Dev Seed Estimate",
            "user_id": user_id,
            "client_id": client_id,
            "responsible": "Development User",
        },
    ).scalar_one()

    conn.execute(
        sa.text(
            """
            INSERT INTO estimate_items
                (name, description, quantity, unit, internal_price, external_price, category, estimate_id)
            VALUES
                ('Sound Engineer', 'On-site engineer support', 10, 'час', 1800, 3200, 'Звук', :estimate_id),
                ('Speaker Set', 'Main PA setup', 1, 'комп.', 12000, 20000, 'Звук', :estimate_id)
            """
        ),
        {"estimate_id": int(estimate_id)},
    )

    conn.execute(
        sa.text(
            """
            INSERT INTO estimate_change_logs (estimate_id, user_id, action, description)
            VALUES (:estimate_id, :user_id, 'Создание', 'Смета создана из dev seed миграции')
            """
        ),
        {"estimate_id": int(estimate_id), "user_id": user_id},
    )

    return int(estimate_id)


def upgrade() -> None:
    if not _is_development():
        return

    conn = op.get_bind()

    user_id = _get_or_create_user(conn)
    client_id = _get_or_create_client(conn, user_id)
    _get_or_create_template(conn, user_id)
    _get_or_create_estimate(conn, user_id, client_id)


def downgrade() -> None:
    if not _is_development():
        return

    conn = op.get_bind()
    user_id = conn.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": DEV_EMAIL},
    ).scalar()
    if not user_id:
        return

    # Explicit cleanup for dev seed entities only.
    conn.execute(
        sa.text(
            """
            DELETE FROM estimates
            WHERE user_id = :user_id AND name = 'Dev Seed Estimate'
            """
        ),
        {"user_id": int(user_id)},
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM estimate_templates
            WHERE user_id = :user_id AND name = 'Dev Event Template'
            """
        ),
        {"user_id": int(user_id)},
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM clients
            WHERE user_id = :user_id AND name = 'Dev Client'
            """
        ),
        {"user_id": int(user_id)},
    )
    conn.execute(
        sa.text("DELETE FROM users WHERE id = :user_id"),
        {"user_id": int(user_id)},
    )
