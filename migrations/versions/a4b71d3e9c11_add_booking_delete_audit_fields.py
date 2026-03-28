"""add booking delete audit fields

Revision ID: a4b71d3e9c11
Revises: 9f31c7d4ab22
Create Date: 2026-03-28 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4b71d3e9c11"
down_revision: Union[str, Sequence[str], None] = "9f31c7d4ab22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("bookings", sa.Column("deleted_by", sa.UUID(), nullable=True))
    op.add_column("bookings", sa.Column("delete_reason", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_bookings_deleted_by_users",
        "bookings",
        "users",
        ["deleted_by"],
        ["uid"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_bookings_deleted_by_users", "bookings", type_="foreignkey")
    op.drop_column("bookings", "delete_reason")
    op.drop_column("bookings", "deleted_by")
