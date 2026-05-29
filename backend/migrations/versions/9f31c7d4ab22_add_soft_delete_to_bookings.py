"""add soft delete to bookings

Revision ID: 9f31c7d4ab22
Revises: 40eaa155f504
Create Date: 2026-03-28 13:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f31c7d4ab22"
down_revision: Union[str, Sequence[str], None] = "40eaa155f504"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("bookings", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index("ix_bookings_deleted_at", "bookings", ["deleted_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_bookings_deleted_at", table_name="bookings")
    op.drop_column("bookings", "deleted_at")
