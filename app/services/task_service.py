"""
Task service for CRUD operations.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, now_ms
from app.schemas.task import TaskCreate, TaskTag, TaskUpdate


class TaskService:
    """Service for task CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        tag: TaskTag | None = None,
        completed: bool | None = None,
        important: bool | None = None,
        include_deleted: bool = False,
    ) -> list[Task]:
        """
        Get all tasks with optional filters.

        Args:
            tag: Filter by tag
            completed: Filter by completion status
            important: Filter by importance
            include_deleted: If True, include soft-deleted tasks
        """
        query = select(Task)

        if not include_deleted:
            query = query.where(Task.deleted_at.is_(None))

        if tag is not None:
            query = query.where(Task.tag == tag.value)

        if completed is not None:
            query = query.where(Task.completed == completed)

        if important is not None:
            query = query.where(Task.important == important)

        query = query.order_by(Task.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, task_in: TaskCreate) -> Task:
        """Create a new task."""
        current_time = now_ms()
        task = Task(
            text=task_in.text,
            description=task_in.description,
            completed=task_in.completed,
            important=task_in.important,
            tag=task_in.tag.value,
            due_at=task_in.due_at,
            recurrence=task_in.recurrence.value,
            recurrence_alt=task_in.recurrence_alt,
            created_at=current_time,
            updated_at=current_time,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update(self, task_id: str, task_in: TaskUpdate) -> Task | None:
        """
        Update an existing task.

        Returns None if task not found.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return None

        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "tag" and value is not None:
                value = value.value
            elif field == "recurrence" and value is not None:
                value = value.value
            setattr(task, field, value)

        task.updated_at = now_ms()
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def soft_delete(self, task_id: str) -> bool:
        """
        Soft delete a task by setting deleted_at.

        Returns True if task was deleted, False if not found.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        task.deleted_at = now_ms()
        task.updated_at = now_ms()
        await self.db.flush()
        return True

    async def hard_delete(self, task_id: str) -> bool:
        """
        Permanently delete a task.

        Returns True if task was deleted, False if not found.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        await self.db.delete(task)
        await self.db.flush()
        return True
