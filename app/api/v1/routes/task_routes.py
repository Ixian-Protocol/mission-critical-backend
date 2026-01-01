"""
Task API routes.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.controllers.task_controller import TaskController
from app.db.session import get_db
from app.schemas.task import (
    SyncRequest,
    SyncResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(tags=["Tasks"])


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Sync tasks",
    description="Bidirectional sync endpoint. Client sends locally modified tasks, "
    "server responds with tasks that have changed since last sync.",
    responses={
        200: {
            "description": "Sync successful",
            "content": {
                "application/json": {
                    "example": {
                        "tasks": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "text": "Buy groceries",
                                "description": "Milk, eggs, bread",
                                "completed": False,
                                "important": True,
                                "tag": "Personal",
                                "due_at": 1704067200000,
                                "recurrence": "weekly",
                                "recurrence_alt": False,
                                "created_at": 1704000000000,
                                "updated_at": 1704060000000,
                                "deleted_at": None,
                            }
                        ],
                        "server_time": 1704067200000,
                        "deleted_ids": [],
                    }
                }
            },
        }
    },
)
async def sync_tasks(
    sync_request: SyncRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    """
    Synchronize tasks between client and server.

    The client sends all locally modified tasks since the last sync,
    and the server responds with any tasks that have changed on the server.

    **Sync Logic:**
    - For each task in request:
      - If task ID doesn't exist on server: INSERT it
      - If task ID exists and client updated_at > server updated_at: UPDATE server
      - If task ID exists and client updated_at <= server updated_at: Skip (server wins)
      - If deleted_at is set: Mark as soft-deleted on server

    **Response includes:**
    - Tasks modified since last_sync_at (that weren't just updated by this request)
    - Current server_time for use as next last_sync_at
    """
    controller = TaskController(db)
    return await controller.sync(sync_request)


@router.get(
    "/tasks",
    response_model=list[TaskResponse],
    summary="List tasks",
    description="Get all non-deleted tasks with optional filtering.",
)
async def get_tasks(
    tag: str | None = Query(None, description="Filter by tag name"),
    completed: bool | None = Query(None, description="Filter by completion status"),
    important: bool | None = Query(None, description="Filter by importance"),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """Get all non-deleted tasks with optional filters."""
    controller = TaskController(db)
    return await controller.get_tasks(tag=tag, completed=completed, important=important)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task",
    description="Get a single task by its ID.",
    responses={
        200: {"description": "Task found"},
        404: {"description": "Task not found"},
    },
)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Get a single task by ID."""
    controller = TaskController(db)
    return await controller.get_task(str(task_id))


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create a new task.",
)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Create a new task."""
    controller = TaskController(db)
    return await controller.create_task(task_in)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update an existing task. Only provided fields are updated.",
    responses={
        200: {"description": "Task updated"},
        404: {"description": "Task not found"},
    },
)
async def update_task(
    task_id: UUID,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Update an existing task."""
    controller = TaskController(db)
    return await controller.update_task(str(task_id), task_in)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Soft-delete a task by setting deleted_at timestamp.",
    responses={
        204: {"description": "Task deleted"},
        404: {"description": "Task not found"},
    },
)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a task."""
    controller = TaskController(db)
    await controller.delete_task(str(task_id))


@router.delete(
    "/tasks/{task_id}/hard",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard delete task",
    description="Permanently delete a task. Use with caution.",
    responses={
        204: {"description": "Task permanently deleted"},
        404: {"description": "Task not found"},
    },
)
async def hard_delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete a task."""
    controller = TaskController(db)
    await controller.hard_delete_task(str(task_id))
