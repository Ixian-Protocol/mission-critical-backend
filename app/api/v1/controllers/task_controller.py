"""
Task controller for handling HTTP requests.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.schemas.task import (
    SyncRequest,
    SyncResponse,
    TaskCreate,
    TaskResponse,
    TaskTag,
    TaskUpdate,
)
from app.services.sync_service import SyncService
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class TaskController:
    """Controller for task-related operations."""

    def __init__(self, db: AsyncSession):
        self.task_service = TaskService(db)
        self.sync_service = SyncService(db)

    async def sync(self, sync_request: SyncRequest) -> SyncResponse:
        """Handle sync request."""
        return await self.sync_service.sync(sync_request)

    async def get_tasks(
        self,
        tag: TaskTag | None = None,
        completed: bool | None = None,
        important: bool | None = None,
    ) -> list[TaskResponse]:
        """Get all tasks with optional filters."""
        tasks = await self.task_service.get_all(
            tag=tag,
            completed=completed,
            important=important,
        )
        return [TaskResponse.model_validate(task) for task in tasks]

    async def get_task(self, task_id: str) -> TaskResponse:
        """Get a single task by ID."""
        task = await self.task_service.get_by_id(task_id)
        if task is None:
            raise NotFoundException(f"Task with id '{task_id}' not found")
        return TaskResponse.model_validate(task)

    async def create_task(self, task_in: TaskCreate) -> TaskResponse:
        """Create a new task."""
        task = await self.task_service.create(task_in)
        return TaskResponse.model_validate(task)

    async def update_task(self, task_id: str, task_in: TaskUpdate) -> TaskResponse:
        """Update an existing task."""
        task = await self.task_service.update(task_id, task_in)
        if task is None:
            raise NotFoundException(f"Task with id '{task_id}' not found")
        return TaskResponse.model_validate(task)

    async def delete_task(self, task_id: str) -> None:
        """Soft delete a task."""
        deleted = await self.task_service.soft_delete(task_id)
        if not deleted:
            raise NotFoundException(f"Task with id '{task_id}' not found")

    async def hard_delete_task(self, task_id: str) -> None:
        """Permanently delete a task."""
        deleted = await self.task_service.hard_delete(task_id)
        if not deleted:
            raise NotFoundException(f"Task with id '{task_id}' not found")
