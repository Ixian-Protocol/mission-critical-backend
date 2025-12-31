# Backend API Specification

This document specifies the REST API endpoints required for the Task sync backend.

## Tech Stack Recommendation

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 + Alembic (migrations)
- **Validation:** Pydantic v2

---

## Database Schema

### Task Table

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text VARCHAR(500) NOT NULL,
    description VARCHAR(2000) NOT NULL DEFAULT '',
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    important BOOLEAN NOT NULL DEFAULT FALSE,
    tag VARCHAR(20) NOT NULL DEFAULT 'General',
    due_at BIGINT NULL,  -- Unix timestamp in milliseconds
    recurrence VARCHAR(10) NOT NULL DEFAULT 'none',
    recurrence_alt BOOLEAN NOT NULL DEFAULT FALSE,
    created_at BIGINT NOT NULL,  -- Unix timestamp in milliseconds
    updated_at BIGINT NOT NULL,  -- Unix timestamp in milliseconds
    deleted_at BIGINT NULL,  -- Soft delete timestamp, NULL if not deleted

    CONSTRAINT valid_tag CHECK (tag IN ('General', 'Work', 'Personal', 'Research', 'Design')),
    CONSTRAINT valid_recurrence CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly'))
);

CREATE INDEX idx_tasks_updated_at ON tasks(updated_at);
CREATE INDEX idx_tasks_deleted_at ON tasks(deleted_at);
```

---

## Pydantic Models

```python
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID

class TaskTag(str, Enum):
    GENERAL = "General"
    WORK = "Work"
    PERSONAL = "Personal"
    RESEARCH = "Research"
    DESIGN = "Design"

class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class TaskBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=2000)
    completed: bool = False
    important: bool = False
    tag: TaskTag = TaskTag.GENERAL
    due_at: int | None = None  # Unix timestamp (ms)
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_alt: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None
    important: bool | None = None
    tag: TaskTag | None = None
    due_at: int | None = None
    recurrence: RecurrenceType | None = None
    recurrence_alt: bool | None = None

class Task(TaskBase):
    id: UUID
    created_at: int  # Unix timestamp (ms)
    updated_at: int  # Unix timestamp (ms)
    deleted_at: int | None = None

    class Config:
        from_attributes = True

class SyncRequest(BaseModel):
    """Client sends tasks that have changed since last sync"""
    tasks: list[Task]
    last_sync_at: int | None = None  # Unix timestamp (ms) of last successful sync

class SyncResponse(BaseModel):
    """Server returns tasks that client needs to update"""
    tasks: list[Task]
    server_time: int  # Current server Unix timestamp (ms)
    deleted_ids: list[UUID]  # IDs of tasks that were hard-deleted on server
```

---

## API Endpoints

### Base URL
```
/api/v1
```

### Sync Endpoint (Primary)

The client uses a single sync endpoint for bidirectional synchronization.

#### `POST /sync`

Synchronizes tasks between client and server. The client sends all locally modified tasks, and the server responds with any tasks that have changed on the server.

**Request Body:**
```json
{
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "text": "Buy groceries",
      "description": "Milk, eggs, bread",
      "completed": false,
      "important": true,
      "tag": "Personal",
      "due_at": 1704067200000,
      "recurrence": "weekly",
      "recurrence_alt": false,
      "created_at": 1704000000000,
      "updated_at": 1704060000000,
      "deleted_at": null
    }
  ],
  "last_sync_at": 1704050000000
}
```

**Response:**
```json
{
  "tasks": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "text": "Task from another device",
      "description": "",
      "completed": false,
      "important": false,
      "tag": "General",
      "due_at": null,
      "recurrence": "none",
      "recurrence_alt": false,
      "created_at": 1704055000000,
      "updated_at": 1704055000000,
      "deleted_at": null
    }
  ],
  "server_time": 1704067200000,
  "deleted_ids": ["770e8400-e29b-41d4-a716-446655440002"]
}
```

**Sync Logic:**

1. **For each task in request:**
   - If task `id` doesn't exist on server: INSERT it
   - If task `id` exists and client `updated_at` > server `updated_at`: UPDATE server
   - If task `id` exists and client `updated_at` <= server `updated_at`: Skip (server wins)
   - If `deleted_at` is set: Mark as soft-deleted on server

2. **Build response:**
   - Return all tasks where `updated_at` > `last_sync_at` (that weren't just updated by this request)
   - Return `deleted_ids` for any tasks hard-deleted since `last_sync_at`

3. **Return `server_time`** so client can use it for next `last_sync_at`

---

### CRUD Endpoints (Optional)

These are optional but useful for debugging and admin purposes.

#### `GET /tasks`

List all non-deleted tasks.

**Query Parameters:**
- `tag` (optional): Filter by tag
- `completed` (optional): Filter by completion status
- `important` (optional): Filter by importance

**Response:** `Task[]`

#### `GET /tasks/{id}`

Get a single task by ID.

**Response:** `Task`

**Errors:**
- `404`: Task not found

#### `POST /tasks`

Create a new task.

**Request Body:** `TaskCreate`

**Response:** `Task` (with generated `id`, `created_at`, `updated_at`)

#### `PATCH /tasks/{id}`

Update a task.

**Request Body:** `TaskUpdate`

**Response:** `Task`

**Errors:**
- `404`: Task not found

#### `DELETE /tasks/{id}`

Soft-delete a task (sets `deleted_at`).

**Response:** `204 No Content`

**Errors:**
- `404`: Task not found

#### `DELETE /tasks/{id}/hard`

Permanently delete a task. Use with caution.

**Response:** `204 No Content`

---

## Error Responses

All errors should follow this format:

```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
- `400`: Bad Request (validation error)
- `404`: Not Found
- `422`: Unprocessable Entity (Pydantic validation failed)
- `500`: Internal Server Error

---

## Timestamps

**Important:** All timestamps are Unix timestamps in **milliseconds** (not seconds). This matches JavaScript's `Date.now()`.

```python
import time

def now_ms() -> int:
    return int(time.time() * 1000)
```

---

## CORS Configuration

The API should allow CORS from the frontend origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "capacitor://localhost",  # iOS
        "http://localhost",       # Android
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Environment Variables

The FastAPI backend should use these environment variables:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/tasks_db
# Optional: for production
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/tasks_db
```

---

## Client Integration

The frontend expects the API URL to be set via:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

The sync flow on the client:

1. Get all tasks with `syncStatus = 'pending'` from IndexedDB
2. POST to `/sync` with these tasks and `last_sync_at`
3. Upsert returned tasks into IndexedDB
4. Hard-delete any tasks in `deleted_ids`
5. Mark synced tasks as `syncStatus = 'synced'`
6. Store `server_time` as new `last_sync_at`

---

## Example FastAPI Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, CORS, routers
│   ├── config.py         # Settings from env vars
│   ├── database.py       # SQLAlchemy engine, session
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py       # SQLAlchemy Task model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py       # Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   └── tasks.py      # Task CRUD + sync endpoints
│   └── services/
│       ├── __init__.py
│       └── sync.py       # Sync logic
├── alembic/              # Migrations
├── alembic.ini
├── requirements.txt
└── pyproject.toml
```

---

## Quick Start Commands

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create tasks table"

# Run migration
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```
