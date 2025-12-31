"""
Task model for the TODO application.
"""
import time
import uuid

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def now_ms() -> int:
    """Return current Unix timestamp in milliseconds."""
    return int(time.time() * 1000)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Task(Base):
    """
    Task model representing a TODO item.

    All timestamps are Unix timestamps in milliseconds to match JavaScript's Date.now().
    """

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Task content
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")

    # Task status flags
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    important: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Categorization
    tag: Mapped[str] = mapped_column(String(20), nullable=False, default="General")

    # Due date (Unix timestamp in milliseconds)
    due_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Recurrence settings
    recurrence: Mapped[str] = mapped_column(String(10), nullable=False, default="none")
    recurrence_alt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps (Unix timestamps in milliseconds)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=now_ms)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=now_ms)

    # Soft delete timestamp
    deleted_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        # Check constraints for enum-like columns
        CheckConstraint(
            "tag IN ('General', 'Work', 'Personal', 'Research', 'Design')",
            name="valid_tag",
        ),
        CheckConstraint(
            "recurrence IN ('none', 'daily', 'weekly', 'monthly')",
            name="valid_recurrence",
        ),
        # Indexes for common queries
        Index("idx_tasks_updated_at", "updated_at"),
        Index("idx_tasks_deleted_at", "deleted_at"),
    )
