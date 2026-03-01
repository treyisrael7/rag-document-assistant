"""Add error_message to documents

Revision ID: 20250228000000
Revises: 20250223000000
Create Date: 2025-02-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250228000000"
down_revision: Union[str, None] = "20250223000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("error_message", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "error_message")
