"""
Data models package.

Import all models here so Alembic can detect them for migrations.
"""
from app.models.user import User

__all__ = ["User"]
