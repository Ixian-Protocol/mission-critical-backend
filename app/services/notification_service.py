"""
Notification service for sending push notifications via ntfy.
"""
import logging
from datetime import datetime

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_ntfy_notification(
    title: str,
    message: str,
    priority: int = 3,
    tags: list[str] | None = None,
) -> bool:
    """
    Send a notification via ntfy.

    Args:
        title: Notification title
        message: Notification body
        priority: 1=min, 2=low, 3=default, 4=high, 5=max
        tags: Optional list of emoji tags (e.g., ["alarm_clock", "task"])

    Returns:
        True if successful, False otherwise.
    """
    if not settings.NTFY_URL:
        logger.debug("NTFY_URL not configured, skipping notification")
        return False

    url = f"{settings.NTFY_URL}/{settings.NTFY_TOPIC}"

    headers = {
        "Title": title,
        "Priority": str(priority),
    }

    if tags:
        headers["Tags"] = ",".join(tags)

    if settings.NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {settings.NTFY_TOKEN}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=message,
                headers=headers,
                timeout=10.0,
            )
            if response.is_success:
                logger.info(f"Sent ntfy notification: {title}")
                return True
            else:
                logger.warning(
                    f"ntfy notification failed with status {response.status_code}: {response.text}"
                )
                return False
    except httpx.RequestError as e:
        logger.error(f"Failed to send ntfy notification: {e}")
        return False


async def send_task_reminder(task_id: str, task_text: str, due_at: int) -> bool:
    """
    Send a task reminder notification.

    Args:
        task_id: UUID of the task
        task_text: Task title/text
        due_at: Due timestamp in milliseconds
    """
    due_time = datetime.fromtimestamp(due_at / 1000)
    time_str = due_time.strftime("%H:%M")

    return await send_ntfy_notification(
        title="Task Reminder",
        message=f"{task_text}\nDue at {time_str}",
        priority=4,  # High priority for reminders
        tags=["alarm_clock", "task"],
    )
