"""
Data models package.

Import all models here so Alembic can detect them for migrations.
"""
from app.models.tag import Tag
from app.models.task import Task

__all__ = ["Tag", "Task"]
