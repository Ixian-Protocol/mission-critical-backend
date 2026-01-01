"""
Tag model for the TODO application.
"""
import uuid

from sqlalchemy import BigInteger, Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.task import now_ms


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Tag(Base):
    """
    Tag model representing a task category.

    All timestamps are Unix timestamps in milliseconds to match JavaScript's Date.now().
    """

    __tablename__ = "tags"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )

    # Tag properties
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color e.g. '#14b8a6'
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps (Unix timestamps in milliseconds)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=now_ms)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=now_ms)

    # Soft delete timestamp
    deleted_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        Index("idx_tags_updated_at", "updated_at"),
        Index("idx_tags_deleted_at", "deleted_at"),
    )
