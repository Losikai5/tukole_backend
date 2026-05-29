"""add soft delete audit fields to reviews

Revision ID: c1d9e8a5f2b4
Revises: a4b71d3e9c11
Create Date: 2026-03-28 13:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d9e8a5f2b4"
down_revision: Union[str, Sequence[str], None] = "a4b71d3e9c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("reviews", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("reviews", sa.Column("deleted_by", sa.UUID(), nullable=True))
    op.add_column("reviews", sa.Column("delete_reason", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_reviews_deleted_by_users",
        "reviews",
        "users",
        ["deleted_by"],
        ["uid"],
    )
    op.create_index("ix_reviews_deleted_at", "reviews", ["deleted_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_reviews_deleted_at", table_name="reviews")
    op.drop_constraint("fk_reviews_deleted_by_users", "reviews", type_="foreignkey")
    op.drop_column("reviews", "delete_reason")
    op.drop_column("reviews", "deleted_by")
    op.drop_column("reviews", "deleted_at")
