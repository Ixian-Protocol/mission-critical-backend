"""
Sync service for bidirectional task synchronization.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, now_ms
from app.schemas.task import SyncRequest, SyncResponse, TaskInSync


class SyncService:
    """Service for handling task synchronization between client and server."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync(self, sync_request: SyncRequest) -> SyncResponse:
        """
        Perform bidirectional sync.

        Logic:
        1. For each incoming task:
           - If task ID doesn't exist on server: INSERT it
           - If task ID exists and client updated_at > server updated_at: UPDATE server
           - If task ID exists and client updated_at <= server updated_at: Skip (server wins)
           - If deleted_at is set: Mark as soft-deleted on server

        2. Build response:
           - Return all tasks where updated_at > last_sync_at (that weren't just updated by this request)
           - Return deleted_ids as empty list (not tracking hard deletes)

        3. Return server_time for client to use as next last_sync_at
        """
        synced_task_ids: set[str] = set()

        # Process incoming tasks
        for client_task in sync_request.tasks:
            task_id = str(client_task.id)
            synced_task_ids.add(task_id)

            # Check if task exists on server
            result = await self.db.execute(select(Task).where(Task.id == task_id))
            server_task = result.scalar_one_or_none()

            if server_task is None:
                # Task doesn't exist - INSERT
                await self._insert_task(client_task)
            elif client_task.updated_at > server_task.updated_at:
                # Client is newer - UPDATE
                await self._update_task(server_task, client_task)
            # else: Server wins - skip

        await self.db.flush()

        # Build response - get tasks modified since last_sync_at
        tasks_to_return: list[Task] = []

        if sync_request.last_sync_at is not None:
            query = select(Task).where(Task.updated_at > sync_request.last_sync_at)
            result = await self.db.execute(query)
            all_modified = list(result.scalars().all())

            # Exclude tasks that were just synced from this request
            # (client already has latest version)
            tasks_to_return = [t for t in all_modified if t.id not in synced_task_ids]
        else:
            # First sync - return all tasks
            result = await self.db.execute(select(Task))
            all_tasks = list(result.scalars().all())
            tasks_to_return = [t for t in all_tasks if t.id not in synced_task_ids]

        # Convert to response schemas
        response_tasks = [
            TaskInSync.model_validate(task) for task in tasks_to_return
        ]

        return SyncResponse(
            tasks=response_tasks,
            server_time=now_ms(),
            deleted_ids=[],  # Not tracking hard deletes per user decision
        )

    async def _insert_task(self, client_task: TaskInSync) -> Task:
        """Insert a new task from sync request."""
        task = Task(
            id=str(client_task.id),
            text=client_task.text,
            description=client_task.description,
            completed=client_task.completed,
            important=client_task.important,
            tag=client_task.tag,
            due_at=client_task.due_at,
            recurrence=client_task.recurrence.value,
            recurrence_alt=client_task.recurrence_alt,
            created_at=client_task.created_at,
            updated_at=client_task.updated_at,
            deleted_at=client_task.deleted_at,
        )
        self.db.add(task)
        return task

    async def _update_task(self, server_task: Task, client_task: TaskInSync) -> None:
        """Update server task with client data."""
        server_task.text = client_task.text
        server_task.description = client_task.description
        server_task.completed = client_task.completed
        server_task.important = client_task.important
        server_task.tag = client_task.tag
        server_task.due_at = client_task.due_at
        server_task.recurrence = client_task.recurrence.value
        server_task.recurrence_alt = client_task.recurrence_alt
        server_task.updated_at = client_task.updated_at
        server_task.deleted_at = client_task.deleted_at
