"""Add uploaded status to documentstatus enum

Revision ID: 20250223000000
Revises: 20250222000000
Create Date: 2025-02-23

"""
from typing import Sequence, Union

from alembic import op

revision: str = "20250223000000"
down_revision: Union[str, None] = "20250222000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'uploaded'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily; would need to recreate type
    pass
