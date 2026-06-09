"""baseline schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-08
"""
from typing import Sequence, Union

from alembic import op

from app.database import Base
from app import models  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)