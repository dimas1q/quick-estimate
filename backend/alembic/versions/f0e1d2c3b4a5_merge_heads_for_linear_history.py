"""merge migration heads for linear history

Revision ID: f0e1d2c3b4a5
Revises: 0123456789ab, bca9045d55b0
Create Date: 2026-03-11 23:58:00
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "f0e1d2c3b4a5"
down_revision: Union[str, tuple[str, str], None] = ("0123456789ab", "bca9045d55b0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
