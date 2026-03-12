"""seed development data only

Revision ID: d1e2f3a4b5c6
Revises: c2d3e4f5a6b7
Create Date: 2026-03-11 23:50:00
"""

from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEV_LOGIN = "dev_demo"
DEV_EMAIL = "dev_demo@example.com"
DEV_PASSWORD = "devpassword"


ESTIMATE_NAMES = [
    "Тестовая смета (базовая)",
    "Тестовая корпоративная встреча",
    "Тестовый запуск продукта",
    "Тестовая фестивальная зона",
    "Тестовый выставочный стенд",
]

TEMPLATE_NAMES = [
    "Тестовый шаблон мероприятия",
    "Тестовый шаблон конференции",
    "Тестовый шаблон концерта",
]

CLIENT_NAMES = [
    "Тестовый клиент",
    "Площадка Альфа",
    "Бета Продакшн",
    "Гамма Студия",
    "Дельта Экспо",
]


def _is_development() -> bool:
    env_name = (os.getenv("APP_ENV") or os.getenv("ENV") or "").lower()
    return env_name in {"dev", "development", "local"}


def _scalar(conn, query: str, params: dict):
    return conn.execute(sa.text(query), params).scalar()


def _get_or_create_user(conn) -> int:
    existing_user_id = _scalar(
        conn,
        "SELECT id FROM users WHERE email = :email",
        {"email": DEV_EMAIL},
    )
    if existing_user_id:
        return int(existing_user_id)

    import bcrypt

    password_hash = bcrypt.hashpw(DEV_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user_id = conn.execute(
        sa.text(
            """
            INSERT INTO users (
                email,
                login,
                name,
                company,
                hashed_password,
                is_admin,
                is_active,
                failed_login_attempts
            )
            VALUES (
                :email,
                :login,
                :name,
                :company,
                :hashed_password,
                false,
                true,
                0
            )
            RETURNING id
            """
        ),
        {
            "email": DEV_EMAIL,
            "login": DEV_LOGIN,
            "name": "Тестовый пользователь",
            "company": "БыстраяСмета Разработка",
            "hashed_password": password_hash,
        },
    ).scalar_one()
    return int(user_id)


def _ensure_client(conn, user_id: int, name: str, company: str, email: str, phone: str) -> int:
    existing_id = _scalar(
        conn,
        """
        SELECT id FROM clients
        WHERE user_id = :user_id AND name = :name
        """,
        {"user_id": user_id, "name": name},
    )
    if existing_id:
        return int(existing_id)

    inserted_id = conn.execute(
        sa.text(
            """
            INSERT INTO clients (name, company, email, phone, user_id)
            VALUES (:name, :company, :email, :phone, :user_id)
            RETURNING id
            """
        ),
        {
            "name": name,
            "company": company,
            "email": email,
            "phone": phone,
            "user_id": user_id,
        },
    ).scalar_one()
    return int(inserted_id)


def _ensure_template(conn, user_id: int, name: str, description: str, items: list[dict]) -> int:
    template_id = _scalar(
        conn,
        """
        SELECT id FROM estimate_templates
        WHERE user_id = :user_id AND name = :name
        """,
        {"user_id": user_id, "name": name},
    )
    if not template_id:
        template_id = conn.execute(
            sa.text(
                """
                INSERT INTO estimate_templates (name, description, use_internal_price, user_id)
                VALUES (:name, :description, true, :user_id)
                RETURNING id
                """
            ),
            {"name": name, "description": description, "user_id": user_id},
        ).scalar_one()

    for item in items:
        existing_item_id = _scalar(
            conn,
            """
            SELECT id FROM estimate_items
            WHERE template_id = :template_id AND name = :name AND category = :category
            """,
            {
                "template_id": int(template_id),
                "name": item["name"],
                "category": item["category"],
            },
        )
        if existing_item_id:
            continue

        conn.execute(
            sa.text(
                """
                INSERT INTO estimate_items
                    (name, description, quantity, unit, internal_price, external_price, category, template_id)
                VALUES
                    (:name, :description, :quantity, :unit, :internal_price, :external_price, :category, :template_id)
                """
            ),
            {**item, "template_id": int(template_id)},
        )

    return int(template_id)


def _ensure_estimate(
    conn,
    user_id: int,
    client_id: int,
    name: str,
    responsible: str,
    status: str,
    use_internal_price: bool,
    items: list[dict],
    add_creation_log: bool = False,
) -> int:
    estimate_id = _scalar(
        conn,
        """
        SELECT id FROM estimates
        WHERE user_id = :user_id AND name = :name
        """,
        {"user_id": user_id, "name": name},
    )

    created_now = False
    if not estimate_id:
        estimate_id = conn.execute(
            sa.text(
                """
                INSERT INTO estimates
                    (
                        name,
                        user_id,
                        client_id,
                        responsible,
                        status,
                        vat_enabled,
                        vat_rate,
                        use_internal_price,
                        read_only
                    )
                VALUES
                    (
                        :name,
                        :user_id,
                        :client_id,
                        :responsible,
                        :status,
                        true,
                        20,
                        :use_internal_price,
                        false
                    )
                RETURNING id
                """
            ),
            {
                "name": name,
                "user_id": user_id,
                "client_id": client_id,
                "responsible": responsible,
                "status": status,
                "use_internal_price": use_internal_price,
            },
        ).scalar_one()
        created_now = True

    for item in items:
        existing_item_id = _scalar(
            conn,
            """
            SELECT id FROM estimate_items
            WHERE estimate_id = :estimate_id AND name = :name AND category = :category
            """,
            {
                "estimate_id": int(estimate_id),
                "name": item["name"],
                "category": item["category"],
            },
        )
        if existing_item_id:
            continue

        conn.execute(
            sa.text(
                """
                INSERT INTO estimate_items
                    (name, description, quantity, unit, internal_price, external_price, category, estimate_id)
                VALUES
                    (:name, :description, :quantity, :unit, :internal_price, :external_price, :category, :estimate_id)
                """
            ),
            {**item, "estimate_id": int(estimate_id)},
        )

    if add_creation_log and created_now:
        conn.execute(
            sa.text(
                """
                INSERT INTO estimate_change_logs (estimate_id, user_id, action, description)
                VALUES (:estimate_id, :user_id, 'Создание', 'Смета создана из миграции тестовых данных')
                """
            ),
            {"estimate_id": int(estimate_id), "user_id": user_id},
        )

    return int(estimate_id)


def _delete_estimate_by_name(conn, user_id: int, estimate_name: str) -> None:
    estimate_id = _scalar(
        conn,
        "SELECT id FROM estimates WHERE user_id = :user_id AND name = :name",
        {"user_id": user_id, "name": estimate_name},
    )
    if not estimate_id:
        return

    estimate_id = int(estimate_id)
    conn.execute(
        sa.text("DELETE FROM estimate_items WHERE estimate_id = :estimate_id"),
        {"estimate_id": estimate_id},
    )
    conn.execute(
        sa.text("DELETE FROM estimate_change_logs WHERE estimate_id = :estimate_id"),
        {"estimate_id": estimate_id},
    )
    conn.execute(
        sa.text("DELETE FROM estimate_favorites WHERE estimate_id = :estimate_id"),
        {"estimate_id": estimate_id},
    )
    conn.execute(
        sa.text("DELETE FROM estimate_versions WHERE estimate_id = :estimate_id"),
        {"estimate_id": estimate_id},
    )
    conn.execute(
        sa.text("DELETE FROM estimates WHERE id = :estimate_id"),
        {"estimate_id": estimate_id},
    )


def _delete_template_by_name(conn, user_id: int, template_name: str) -> None:
    template_id = _scalar(
        conn,
        "SELECT id FROM estimate_templates WHERE user_id = :user_id AND name = :name",
        {"user_id": user_id, "name": template_name},
    )
    if not template_id:
        return

    template_id = int(template_id)
    conn.execute(
        sa.text("DELETE FROM estimate_items WHERE template_id = :template_id"),
        {"template_id": template_id},
    )
    conn.execute(
        sa.text("DELETE FROM estimate_templates WHERE id = :template_id"),
        {"template_id": template_id},
    )


def _delete_client_by_name(conn, user_id: int, client_name: str) -> None:
    conn.execute(
        sa.text("DELETE FROM clients WHERE user_id = :user_id AND name = :name"),
        {"user_id": user_id, "name": client_name},
    )


def upgrade() -> None:
    if not _is_development():
        return

    conn = op.get_bind()
    user_id = _get_or_create_user(conn)

    clients = [
        ("Тестовый клиент", "Тестовый клиент", "qa.client@example.com", "+7-495-555-0101"),
        ("Площадка Альфа", "Альфа Ивентс", "alpha@example.com", "+7-495-555-2001"),
        ("Бета Продакшн", "Бета Прод", "beta@example.com", "+7-495-555-2002"),
        ("Гамма Студия", "Гамма Студия", "gamma@example.com", "+7-495-555-2003"),
        ("Дельта Экспо", "Дельта Экспо Групп", "delta@example.com", "+7-495-555-2004"),
    ]
    client_ids: dict[str, int] = {}
    for name, company, email, phone in clients:
        client_ids[name] = _ensure_client(conn, user_id, name, company, email, phone)

    _ensure_template(
        conn,
        user_id,
        "Тестовый шаблон мероприятия",
        "Шаблон с типовыми позициями услуг для разработки.",
        [
            {
                "name": "Монтаж сцены",
                "description": "Сборка сценического оборудования",
                "quantity": 1,
                "unit": "проект",
                "internal_price": 25000,
                "external_price": 42000,
                "category": "Сцена",
            },
            {
                "name": "Пакет света",
                "description": "Базовый комплект светового оборудования",
                "quantity": 8,
                "unit": "час",
                "internal_price": 3500,
                "external_price": 6000,
                "category": "Свет",
            },
        ],
    )
    _ensure_template(
        conn,
        user_id,
        "Тестовый шаблон конференции",
        "Шаблон для подготовки и проведения конференции.",
        [
            {
                "name": "Светодиодный экран",
                "description": "Комплект светодиодного экрана для главной сцены",
                "quantity": 1,
                "unit": "комп.",
                "internal_price": 50000,
                "external_price": 85000,
                "category": "Видео",
            },
            {
                "name": "Радиомикрофоны",
                "description": "Комплект беспроводных микрофонов",
                "quantity": 6,
                "unit": "шт",
                "internal_price": 1200,
                "external_price": 2500,
                "category": "Звук",
            },
        ],
    )
    _ensure_template(
        conn,
        user_id,
        "Тестовый шаблон концерта",
        "Шаблон для концертного света и звука.",
        [
            {
                "name": "Линейный массив",
                "description": "Большой комплект линейного массива",
                "quantity": 1,
                "unit": "комп.",
                "internal_price": 90000,
                "external_price": 140000,
                "category": "Звук",
            },
            {
                "name": "Поворотные головы",
                "description": "Комплект поворотных световых приборов",
                "quantity": 16,
                "unit": "шт",
                "internal_price": 2000,
                "external_price": 4500,
                "category": "Свет",
            },
        ],
    )

    estimate_payloads = [
        (
            "Тестовая смета (базовая)",
            client_ids["Тестовый клиент"],
            "Тестовый пользователь",
            "draft",
            True,
            True,
            [
                {
                    "name": "Звукорежиссер",
                    "description": "Работа звукорежиссера на площадке",
                    "quantity": 10,
                    "unit": "час",
                    "internal_price": 1800,
                    "external_price": 3200,
                    "category": "Звук",
                },
                {
                    "name": "Комплект акустики",
                    "description": "Основной комплект звукового оборудования",
                    "quantity": 1,
                    "unit": "комп.",
                    "internal_price": 12000,
                    "external_price": 20000,
                    "category": "Звук",
                },
            ],
        ),
        (
            "Тестовая корпоративная встреча",
            client_ids["Площадка Альфа"],
            "Тестовый пользователь",
            "draft",
            True,
            False,
            [
                {
                    "name": "Сборка сцены",
                    "description": "Монтаж и демонтаж сценической конструкции",
                    "quantity": 1,
                    "unit": "проект",
                    "internal_price": 30000,
                    "external_price": 52000,
                    "category": "Сцена",
                },
                {
                    "name": "Звуковой пульт",
                    "description": "Смена фронтового звукорежиссера",
                    "quantity": 12,
                    "unit": "час",
                    "internal_price": 1700,
                    "external_price": 3000,
                    "category": "Звук",
                },
            ],
        ),
        (
            "Тестовый запуск продукта",
            client_ids["Бета Продакшн"],
            "Тестовый пользователь",
            "sent",
            True,
            False,
            [
                {
                    "name": "Проекционная система",
                    "description": "Настройка двух проекторов",
                    "quantity": 1,
                    "unit": "комп.",
                    "internal_price": 22000,
                    "external_price": 40000,
                    "category": "Видео",
                },
                {
                    "name": "Декоративный свет",
                    "description": "Пакет фонового освещения площадки",
                    "quantity": 1,
                    "unit": "проект",
                    "internal_price": 18000,
                    "external_price": 30000,
                    "category": "Свет",
                },
            ],
        ),
        (
            "Тестовая фестивальная зона",
            client_ids["Гамма Студия"],
            "Тестовый пользователь",
            "approved",
            False,
            False,
            [
                {
                    "name": "Диджей-стойка",
                    "description": "Аренда и настройка диджей-стойки",
                    "quantity": 2,
                    "unit": "день",
                    "internal_price": 8000,
                    "external_price": 16000,
                    "category": "Аренда",
                },
                {
                    "name": "Бэклайн-комплект",
                    "description": "Стандартный комплект бэклайна",
                    "quantity": 1,
                    "unit": "комп.",
                    "internal_price": 14000,
                    "external_price": 26000,
                    "category": "Звук",
                },
            ],
        ),
        (
            "Тестовый выставочный стенд",
            client_ids["Дельта Экспо"],
            "Тестовый пользователь",
            "paid",
            True,
            False,
            [
                {
                    "name": "Брендирование стенда",
                    "description": "Дизайн и нанесение фирменной графики",
                    "quantity": 1,
                    "unit": "проект",
                    "internal_price": 25000,
                    "external_price": 45000,
                    "category": "Дизайн",
                },
                {
                    "name": "Промо-персонал",
                    "description": "Смены промоутеров на площадке",
                    "quantity": 16,
                    "unit": "час",
                    "internal_price": 900,
                    "external_price": 1800,
                    "category": "Персонал",
                },
            ],
        ),
    ]

    for payload in estimate_payloads:
        _ensure_estimate(
            conn,
            user_id,
            payload[1],
            payload[0],
            payload[2],
            payload[3],
            payload[4],
            payload[6],
            add_creation_log=payload[5],
        )


def downgrade() -> None:
    if not _is_development():
        return

    conn = op.get_bind()
    user_id = _scalar(
        conn,
        "SELECT id FROM users WHERE email = :email",
        {"email": DEV_EMAIL},
    )
    if not user_id:
        return

    user_id = int(user_id)

    for estimate_name in ESTIMATE_NAMES:
        _delete_estimate_by_name(conn, user_id, estimate_name)

    for template_name in TEMPLATE_NAMES:
        _delete_template_by_name(conn, user_id, template_name)

    for client_name in CLIENT_NAMES:
        _delete_client_by_name(conn, user_id, client_name)

    conn.execute(
        sa.text("DELETE FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
