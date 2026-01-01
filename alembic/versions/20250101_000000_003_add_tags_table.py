"""Add tags table and remove valid_tag constraint from tasks

Revision ID: 003
Revises: 002
Create Date: 2025-01-01 00:00:00.000000
"""
import time
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def now_ms() -> int:
    """Return current Unix timestamp in milliseconds."""
    return int(time.time() * 1000)


def upgrade() -> None:
    """Create tags table, seed defaults, and remove constraint from tasks."""
    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("deleted_at", sa.BigInteger(), nullable=True),
    )

    # Create indexes
    op.create_index("idx_tags_updated_at", "tags", ["updated_at"])
    op.create_index("idx_tags_deleted_at", "tags", ["deleted_at"])

    # Remove valid_tag constraint from tasks table
    op.drop_constraint("valid_tag", "tasks", type_="check")

    # Seed default tags
    current_time = now_ms()
    default_tags = [
        {"name": "General", "color": "#14b8a6"},
        {"name": "Work", "color": "#a855f7"},
        {"name": "Personal", "color": "#3b82f6"},
        {"name": "Research", "color": "#22c55e"},
        {"name": "Design", "color": "#ec4899"},
    ]

    tags_table = sa.table(
        "tags",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("color", sa.String),
        sa.column("is_default", sa.Boolean),
        sa.column("created_at", sa.BigInteger),
        sa.column("updated_at", sa.BigInteger),
    )

    for tag in default_tags:
        op.execute(
            tags_table.insert().values(
                id=str(uuid.uuid4()),
                name=tag["name"],
                color=tag["color"],
                is_default=True,
                created_at=current_time,
                updated_at=current_time,
            )
        )


def downgrade() -> None:
    """Drop tags table and restore valid_tag constraint."""
    # Drop tags table and indexes
    op.drop_index("idx_tags_deleted_at", table_name="tags")
    op.drop_index("idx_tags_updated_at", table_name="tags")
    op.drop_table("tags")

    # Restore valid_tag constraint on tasks table
    op.create_check_constraint(
        "valid_tag",
        "tasks",
        "tag IN ('General', 'Work', 'Personal', 'Research', 'Design')",
    )
