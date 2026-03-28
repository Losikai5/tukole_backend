"""extend notifications with metadata and indexes

Revision ID: d2c4f9a1b8e7
Revises: 68422507bf4e
Create Date: 2026-03-28 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d2c4f9a1b8e7"
down_revision: Union[str, Sequence[str], None] = "68422507bf4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("notifications", sa.Column("event_type", sa.String(length=100), nullable=True))
    op.add_column("notifications", sa.Column("entity_type", sa.String(length=100), nullable=True))
    op.add_column("notifications", sa.Column("entity_id", sa.UUID(), nullable=True))
    op.add_column("notifications", sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_index("ix_notifications_user_created_at", "notifications", ["user_id", "created_at"], unique=False)
    op.create_index("ix_notifications_user_is_read", "notifications", ["user_id", "is_read"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_notifications_user_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_created_at", table_name="notifications")

    op.drop_column("notifications", "payload")
    op.drop_column("notifications", "entity_id")
    op.drop_column("notifications", "entity_type")
    op.drop_column("notifications", "event_type")
