"""Replace users table with tasks table

Revision ID: 002
Revises: 001
Create Date: 2024-12-31 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop users table and create tasks table."""
    # Drop users table
    op.drop_table("users")

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False, server_default=""),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("important", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tag", sa.String(20), nullable=False, server_default="General"),
        sa.Column("due_at", sa.BigInteger(), nullable=True),
        sa.Column("recurrence", sa.String(10), nullable=False, server_default="none"),
        sa.Column("recurrence_alt", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("deleted_at", sa.BigInteger(), nullable=True),
        sa.CheckConstraint(
            "tag IN ('General', 'Work', 'Personal', 'Research', 'Design')",
            name="valid_tag",
        ),
        sa.CheckConstraint(
            "recurrence IN ('none', 'daily', 'weekly', 'monthly')",
            name="valid_recurrence",
        ),
    )

    # Create indexes
    op.create_index("idx_tasks_updated_at", "tasks", ["updated_at"])
    op.create_index("idx_tasks_deleted_at", "tasks", ["deleted_at"])


def downgrade() -> None:
    """Drop tasks table and restore users table."""
    # Drop tasks table and indexes
    op.drop_index("idx_tasks_deleted_at", table_name="tasks")
    op.drop_index("idx_tasks_updated_at", table_name="tasks")
    op.drop_table("tasks")

    # Restore users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
