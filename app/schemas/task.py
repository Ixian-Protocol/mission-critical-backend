"""
Pydantic schemas for Task API.
"""
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecurrenceType(str, Enum):
    """Valid recurrence types."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TaskBase(BaseModel):
    """Base schema with common task fields."""

    text: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=2000)
    completed: bool = False
    important: bool = False
    tag: str = Field(default="General", max_length=50)  # Now dynamic - references tag name
    due_at: int | None = None  # Unix timestamp (ms)
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_alt: bool = False


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    pass


class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields optional."""

    text: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
    important: bool | None = None
    tag: str | None = Field(default=None, max_length=50)
    due_at: int | None = None
    recurrence: RecurrenceType | None = None
    recurrence_alt: bool | None = None


class TaskResponse(TaskBase):
    """Schema for task responses including server-generated fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: int  # Unix timestamp (ms)
    updated_at: int  # Unix timestamp (ms)
    deleted_at: int | None = None


class TaskInSync(TaskBase):
    """Schema for tasks in sync request/response (includes all fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: int  # Unix timestamp (ms)
    updated_at: int  # Unix timestamp (ms)
    deleted_at: int | None = None


class SyncRequest(BaseModel):
    """Request body for sync endpoint."""

    tasks: list[TaskInSync]
    last_sync_at: int | None = None  # Unix timestamp (ms) of last successful sync


class SyncResponse(BaseModel):
    """Response body for sync endpoint."""

    tasks: list[TaskInSync]
    server_time: int  # Current server Unix timestamp (ms)
    deleted_ids: list[UUID]  # IDs of tasks that were hard-deleted on server
