"""
SQLAlchemy declarative base and common model mixins.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    All models should inherit from this class:
        class User(Base):
            __tablename__ = "users"
            ...
    """
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.

    Usage:
        class User(Base, TimestampMixin):
            __tablename__ = "users"
            ...
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TableNameMixin:
    """
    Mixin that automatically generates table name from class name.

    Converts CamelCase to snake_case and pluralizes.
    Example: UserProfile -> user_profiles
    """
    @classmethod
    def __tablename__(cls) -> str:
        import re
        # Convert CamelCase to snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Simple pluralization (add 's')
        return f"{name}s"
