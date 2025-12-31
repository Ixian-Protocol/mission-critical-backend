# ntfy Task Reminder Notifications

This document specifies the backend implementation for sending task reminder
notifications via [ntfy](https://ntfy.sh).

## Overview

The system sends push notifications to users 15 minutes before a task's due
time. Notifications are delivered via ntfy, which the client subscribes to using
Server-Sent Events (SSE).

### Architecture

```
┌─────────────┐    SSE Subscribe     ┌─────────────┐
│   Client    │ ◄──────────────────► │ ntfy Server │
│  (Mobile)   │                      │             │
└─────────────┘                      └─────────────┘
                                           ▲
                                           │ POST /topic
                                           │
                                     ┌─────────────┐
                                     │   FastAPI   │
                                     │   Backend   │
                                     │ (Scheduler) │
                                     └─────────────┘
```

**Fixed Topic Name:** `ixian-mission-critical`

---

## Backend Requirements

### Dependencies

Add to `requirements.txt`:

```
apscheduler>=3.10.0
httpx>=0.27.0
```

Or with poetry/pip:

```bash
pip install apscheduler httpx
```

### Environment Variables

```bash
# ntfy server URL (required for notifications)
NTFY_URL=https://ntfy.sh
# or self-hosted: NTFY_URL=https://ntfy.example.com

# Optional: ntfy authentication (if your server requires it)
NTFY_TOKEN=tk_your_token_here
```

---

## Implementation

### 1. Configuration (`app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    ntfy_url: str | None = None
    ntfy_token: str | None = None
    ntfy_topic: str = "ixian-mission-critical"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Notification Service (`app/services/notifications.py`)

```python
import httpx
from app.config import settings

async def send_ntfy_notification(
    title: str,
    message: str,
    priority: int = 3,  # 1=min, 2=low, 3=default, 4=high, 5=max
    tags: list[str] | None = None,
    click_url: str | None = None,
) -> bool:
    """
    Send a notification via ntfy.

    Returns True if successful, False otherwise.
    """
    if not settings.ntfy_url:
        return False

    url = f"{settings.ntfy_url}/{settings.ntfy_topic}"

    headers = {
        "Title": title,
        "Priority": str(priority),
    }

    if tags:
        headers["Tags"] = ",".join(tags)

    if click_url:
        headers["Click"] = click_url

    if settings.ntfy_token:
        headers["Authorization"] = f"Bearer {settings.ntfy_token}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=message,
                headers=headers,
                timeout=10.0,
            )
            return response.is_success
    except httpx.RequestError as e:
        print(f"Failed to send ntfy notification: {e}")
        return False


async def send_task_reminder(task_id: str, task_text: str, due_at: int) -> bool:
    """
    Send a task reminder notification.

    Args:
        task_id: UUID of the task
        task_text: Task title/text
        due_at: Due timestamp in milliseconds
    """
    from datetime import datetime

    due_time = datetime.fromtimestamp(due_at / 1000)
    time_str = due_time.strftime("%H:%M")

    return await send_ntfy_notification(
        title="Task Reminder",
        message=f"{task_text}\nDue at {time_str}",
        priority=4,  # High priority for reminders
        tags=["alarm_clock", "task"],
    )
```

### 3. Scheduler Setup (`app/scheduler.py`)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.database import async_session_maker
from app.models.task import Task
from app.services.notifications import send_task_reminder

scheduler = AsyncIOScheduler()


def now_ms() -> int:
    """Current time in milliseconds."""
    return int(datetime.now().timestamp() * 1000)


async def check_upcoming_tasks():
    """
    Check for tasks due in the next 15-16 minutes and send reminders.
    Runs every minute.
    """
    now = now_ms()
    # Window: 15 minutes from now (+/- 30 seconds to account for scheduler drift)
    reminder_window_start = now + (15 * 60 * 1000) - 30000  # 14:30 from now
    reminder_window_end = now + (15 * 60 * 1000) + 30000    # 15:30 from now

    async with async_session_maker() as session:
        # Find tasks:
        # - Have a due_at in the reminder window
        # - Not completed
        # - Not deleted
        # - Haven't been reminded yet (optional: track this)
        stmt = select(Task).where(
            and_(
                Task.due_at.isnot(None),
                Task.due_at >= reminder_window_start,
                Task.due_at <= reminder_window_end,
                Task.completed == False,
                Task.deleted_at.is_(None),
            )
        )

        result = await session.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            success = await send_task_reminder(
                task_id=str(task.id),
                task_text=task.text,
                due_at=task.due_at,
            )
            if success:
                print(f"Sent reminder for task: {task.text}")
            else:
                print(f"Failed to send reminder for task: {task.text}")


def start_scheduler():
    """Start the background scheduler."""
    scheduler.add_job(
        check_upcoming_tasks,
        trigger=IntervalTrigger(minutes=1),
        id="task_reminders",
        name="Check for tasks due in 15 minutes",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown(wait=False)
```

### 4. Integrate with FastAPI (`app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.scheduler import start_scheduler, stop_scheduler
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.ntfy_url:
        print(f"Starting scheduler with ntfy notifications to {settings.ntfy_url}")
        start_scheduler()
    else:
        print("NTFY_URL not configured, task reminders disabled")

    yield

    # Shutdown
    stop_scheduler()

app = FastAPI(lifespan=lifespan)

# ... rest of your app setup
```

---

## Preventing Duplicate Reminders

To avoid sending multiple reminders for the same task, you can either:

### Option A: Track reminded tasks in memory (simple)

```python
# In scheduler.py
reminded_task_ids: set[str] = set()

async def check_upcoming_tasks():
    # ... query tasks ...

    for task in tasks:
        task_id = str(task.id)
        if task_id in reminded_task_ids:
            continue

        success = await send_task_reminder(...)
        if success:
            reminded_task_ids.add(task_id)

    # Clean up old entries (tasks more than 1 hour past due)
    # This prevents memory growth
    one_hour_ago = now_ms() - (60 * 60 * 1000)
    # ... cleanup logic ...
```

### Option B: Add a database column (persistent)

```sql
ALTER TABLE tasks ADD COLUMN reminder_sent_at BIGINT NULL;
```

```python
# Only select tasks that haven't been reminded
stmt = select(Task).where(
    and_(
        Task.due_at.isnot(None),
        Task.due_at >= reminder_window_start,
        Task.due_at <= reminder_window_end,
        Task.completed == False,
        Task.deleted_at.is_(None),
        Task.reminder_sent_at.is_(None),  # Not yet reminded
    )
)

# After sending reminder
task.reminder_sent_at = now_ms()
await session.commit()
```

---

## ntfy Message Format

The notification sent to ntfy follows this format:

**HTTP Request:**

```http
POST /ixian-mission-critical HTTP/1.1
Host: ntfy.sh
Title: Task Reminder
Priority: 4
Tags: alarm_clock,task

Buy groceries
Due at 14:30
```

**JSON equivalent** (if using JSON endpoint):

```json
{
  "topic": "ixian-mission-critical",
  "title": "Task Reminder",
  "message": "Buy groceries\nDue at 14:30",
  "priority": 4,
  "tags": ["alarm_clock", "task"]
}
```

---

## Testing

### Manual Test

```bash
# Send a test notification
curl -X POST "https://ntfy.sh/ixian-mission-critical" \
  -H "Title: Test Reminder" \
  -H "Priority: 4" \
  -H "Tags: test" \
  -d "This is a test notification"
```

### Unit Test

```python
import pytest
from unittest.mock import patch, AsyncMock
from app.services.notifications import send_task_reminder

@pytest.mark.asyncio
async def test_send_task_reminder():
    with patch("app.services.notifications.httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        result = await send_task_reminder(
            task_id="123",
            task_text="Test task",
            due_at=1704067200000,
        )

        assert result is True
```

---

## Self-Hosted ntfy

If using a self-hosted ntfy server:

1. Deploy ntfy: https://docs.ntfy.sh/install/

2. Configure authentication (recommended):
   ```yaml
   # /etc/ntfy/server.yml
   auth-file: /var/lib/ntfy/user.db
   auth-default-access: deny-all
   ```

3. Create access token:
   ```bash
   ntfy token add --user=myuser
   ```

4. Set `NTFY_TOKEN` in your backend environment.

5. The client only needs the ntfy URL - it subscribes read-only to the topic.

---

## Sync Endpoint Update (Optional)

If you want to include ntfy configuration status in the sync response:

```python
class SyncResponse(BaseModel):
    tasks: list[Task]
    server_time: int
    deleted_ids: list[UUID]
    notifications_enabled: bool = False  # New field

# In sync endpoint
return SyncResponse(
    tasks=tasks_to_return,
    server_time=now_ms(),
    deleted_ids=deleted_ids,
    notifications_enabled=bool(settings.ntfy_url),
)
```

---

## Summary

| Component               | File                           | Purpose                          |
| ----------------------- | ------------------------------ | -------------------------------- |
| Configuration           | `app/config.py`                | Load ntfy settings from env      |
| Notification Service    | `app/services/notifications.py`| Send notifications via ntfy      |
| Scheduler               | `app/scheduler.py`             | Check for upcoming tasks         |
| FastAPI Integration     | `app/main.py`                  | Start/stop scheduler on app lifecycle |

The scheduler runs every minute, checks for tasks due in ~15 minutes, and sends
a high-priority notification via ntfy. The client receives these via SSE
subscription to the `ixian-mission-critical` topic.
