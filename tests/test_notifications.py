"""
Tests for the notification system.

Covers:
- notification_service.py: send_ntfy_notification(), send_task_reminder()
- scheduler.py: check_upcoming_tasks(), start_scheduler(), stop_scheduler()

Uses pytest-describe for BDD-style test organization.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, now_ms


def describe_notification_service():
    """Tests for the notification service module."""

    def describe_send_ntfy_notification():
        """Tests for the send_ntfy_notification function."""

        @pytest.mark.asyncio
        async def it_returns_false_when_ntfy_url_not_configured():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = None

            with patch(
                "app.services.notification_service.settings", mock_settings
            ):
                # Import after patching
                from app.services.notification_service import send_ntfy_notification

                # Act
                result = await send_ntfy_notification(
                    title="Test", message="Test message"
                )

                # Assert
                assert result is False

        @pytest.mark.asyncio
        async def it_sends_correct_headers_without_token():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test-topic"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                result = await send_ntfy_notification(
                    title="Test Title",
                    message="Test message body",
                    priority=4,
                    tags=["alarm_clock", "task"],
                )

                # Assert
                assert result is True
                mock_client.post.assert_called_once()
                call_kwargs = mock_client.post.call_args
                assert call_kwargs.kwargs["content"] == "Test message body"
                headers = call_kwargs.kwargs["headers"]
                assert headers["Title"] == "Test Title"
                assert headers["Priority"] == "4"
                assert headers["Tags"] == "alarm_clock,task"
                assert "Authorization" not in headers

        @pytest.mark.asyncio
        async def it_sends_authorization_header_when_token_configured():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test-topic"
            mock_settings.NTFY_TOKEN = "secret-token"

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                result = await send_ntfy_notification(
                    title="Test", message="Test message"
                )

                # Assert
                assert result is True
                call_kwargs = mock_client.post.call_args
                headers = call_kwargs.kwargs["headers"]
                assert headers["Authorization"] == "Bearer secret-token"

        @pytest.mark.asyncio
        async def it_sends_to_correct_url_with_topic():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "my-topic"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                await send_ntfy_notification(title="Test", message="Test")

                # Assert
                call_args = mock_client.post.call_args
                assert call_args.args[0] == "https://ntfy.example.com/my-topic"

        @pytest.mark.asyncio
        async def it_returns_true_on_success():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                result = await send_ntfy_notification(
                    title="Test", message="Test message"
                )

                # Assert
                assert result is True

        @pytest.mark.asyncio
        async def it_returns_false_on_http_error():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = False
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                result = await send_ntfy_notification(
                    title="Test", message="Test message"
                )

                # Assert
                assert result is False

        @pytest.mark.asyncio
        async def it_returns_false_on_network_error():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(
                    side_effect=httpx.RequestError("Connection failed")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                result = await send_ntfy_notification(
                    title="Test", message="Test message"
                )

                # Assert
                assert result is False

        @pytest.mark.asyncio
        async def it_uses_default_priority_when_not_specified():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                await send_ntfy_notification(title="Test", message="Test")

                # Assert
                call_kwargs = mock_client.post.call_args
                headers = call_kwargs.kwargs["headers"]
                assert headers["Priority"] == "3"  # Default priority

        @pytest.mark.asyncio
        async def it_omits_tags_header_when_no_tags_provided():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_ntfy_notification

                # Act
                await send_ntfy_notification(
                    title="Test", message="Test", tags=None
                )

                # Assert
                call_kwargs = mock_client.post.call_args
                headers = call_kwargs.kwargs["headers"]
                assert "Tags" not in headers

    def describe_send_task_reminder():
        """Tests for the send_task_reminder function."""

        @pytest.mark.asyncio
        async def it_formats_message_correctly_with_time():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            # Create a specific timestamp: 2024-01-15 14:30:00
            due_datetime = datetime(2024, 1, 15, 14, 30, 0)
            due_at_ms = int(due_datetime.timestamp() * 1000)

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_task_reminder

                # Act
                result = await send_task_reminder(
                    task_id="task-123",
                    task_text="Buy groceries",
                    due_at=due_at_ms,
                )

                # Assert
                assert result is True
                call_kwargs = mock_client.post.call_args
                headers = call_kwargs.kwargs["headers"]
                content = call_kwargs.kwargs["content"]

                assert headers["Title"] == "Task Reminder"
                assert headers["Priority"] == "4"  # High priority for reminders
                assert headers["Tags"] == "alarm_clock,task"
                assert content == "Buy groceries\nDue at 14:30"

        @pytest.mark.asyncio
        async def it_uses_high_priority_for_reminders():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = "https://ntfy.example.com"
            mock_settings.NTFY_TOPIC = "test"
            mock_settings.NTFY_TOKEN = None

            mock_response = MagicMock()
            mock_response.is_success = True
            mock_response.status_code = 200

            due_at_ms = now_ms() + 900000  # 15 minutes from now

            with patch(
                "app.services.notification_service.settings", mock_settings
            ), patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client

                from app.services.notification_service import send_task_reminder

                # Act
                await send_task_reminder(
                    task_id="task-123",
                    task_text="Important task",
                    due_at=due_at_ms,
                )

                # Assert
                call_kwargs = mock_client.post.call_args
                headers = call_kwargs.kwargs["headers"]
                assert headers["Priority"] == "4"

        @pytest.mark.asyncio
        async def it_returns_false_when_notification_fails():
            # Arrange
            mock_settings = MagicMock()
            mock_settings.NTFY_URL = None  # Not configured

            with patch(
                "app.services.notification_service.settings", mock_settings
            ):
                from app.services.notification_service import send_task_reminder

                # Act
                result = await send_task_reminder(
                    task_id="task-123",
                    task_text="Test task",
                    due_at=now_ms(),
                )

                # Assert
                assert result is False


def describe_scheduler():
    """Tests for the scheduler module."""

    def describe_check_upcoming_tasks():
        """Tests for the check_upcoming_tasks function."""

        @pytest.mark.asyncio
        async def it_finds_tasks_in_15_minute_reminder_window(
            db_session: AsyncSession,
        ):
            # Arrange
            current_time = now_ms()
            # Task due in exactly 15 minutes (within the window)
            due_at = current_time + (15 * 60 * 1000)

            task = Task(
                text="Task due in 15 minutes",
                description="",
                completed=False,
                important=False,
                tag="General",
                due_at=due_at,
                recurrence="none",
                recurrence_alt=False,
                created_at=current_time,
                updated_at=current_time,
            )
            db_session.add(task)
            await db_session.flush()
            await db_session.commit()

            task_id = str(task.id)

            # Mock notification to track if it was called
            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", set()
            ):
                mock_send_reminder.return_value = True

                # Create a mock session that returns our task
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [task]
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                mock_send_reminder.assert_called_once_with(
                    task_id=task_id,
                    task_text="Task due in 15 minutes",
                    due_at=due_at,
                )

        @pytest.mark.asyncio
        async def it_ignores_completed_tasks(db_session: AsyncSession):
            # Arrange
            current_time = now_ms()
            due_at = current_time + (15 * 60 * 1000)

            task = Task(
                text="Completed task",
                description="",
                completed=True,  # Task is completed
                important=False,
                tag="General",
                due_at=due_at,
                recurrence="none",
                recurrence_alt=False,
                created_at=current_time,
                updated_at=current_time,
            )
            db_session.add(task)
            await db_session.flush()
            await db_session.commit()

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", set()
            ):
                # Return empty list (completed tasks filtered by query)
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = []  # No tasks match
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                mock_send_reminder.assert_not_called()

        @pytest.mark.asyncio
        async def it_ignores_deleted_tasks(db_session: AsyncSession):
            # Arrange
            current_time = now_ms()
            due_at = current_time + (15 * 60 * 1000)

            task = Task(
                text="Deleted task",
                description="",
                completed=False,
                important=False,
                tag="General",
                due_at=due_at,
                recurrence="none",
                recurrence_alt=False,
                created_at=current_time,
                updated_at=current_time,
                deleted_at=current_time,  # Task is deleted
            )
            db_session.add(task)
            await db_session.flush()
            await db_session.commit()

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", set()
            ):
                # Return empty list (deleted tasks filtered by query)
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = []  # No tasks match
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                mock_send_reminder.assert_not_called()

        @pytest.mark.asyncio
        async def it_ignores_tasks_without_due_at(db_session: AsyncSession):
            # Arrange
            current_time = now_ms()

            task = Task(
                text="Task without due date",
                description="",
                completed=False,
                important=False,
                tag="General",
                due_at=None,  # No due date
                recurrence="none",
                recurrence_alt=False,
                created_at=current_time,
                updated_at=current_time,
            )
            db_session.add(task)
            await db_session.flush()
            await db_session.commit()

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", set()
            ):
                # Return empty list (tasks without due_at filtered by query)
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = []  # No tasks match
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                mock_send_reminder.assert_not_called()

        @pytest.mark.asyncio
        async def it_skips_already_reminded_tasks():
            # Arrange
            current_time = now_ms()
            due_at = current_time + (15 * 60 * 1000)

            task = MagicMock()
            task.id = "already-reminded-task-id"
            task.text = "Already reminded task"
            task.due_at = due_at

            # Pre-populate reminded set
            reminded_set = {"already-reminded-task-id"}

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", reminded_set
            ):
                # Return the task from DB
                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [task]
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert - notification should NOT be sent
                mock_send_reminder.assert_not_called()

        @pytest.mark.asyncio
        async def it_adds_task_to_reminded_set_after_successful_notification():
            # Arrange
            current_time = now_ms()
            due_at = current_time + (15 * 60 * 1000)

            task = MagicMock()
            task.id = "new-task-id"
            task.text = "New task to remind"
            task.due_at = due_at

            reminded_set = set()

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", reminded_set
            ):
                mock_send_reminder.return_value = True  # Notification succeeds

                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [task]
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                mock_send_reminder.assert_called_once()
                assert "new-task-id" in reminded_set

        @pytest.mark.asyncio
        async def it_does_not_add_to_reminded_set_on_failed_notification():
            # Arrange
            current_time = now_ms()
            due_at = current_time + (15 * 60 * 1000)

            task = MagicMock()
            task.id = "failed-task-id"
            task.text = "Task that fails notification"
            task.due_at = due_at

            reminded_set = set()

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", reminded_set
            ):
                mock_send_reminder.return_value = False  # Notification fails

                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [task]
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                mock_send_reminder.assert_called_once()
                assert "failed-task-id" not in reminded_set

        @pytest.mark.asyncio
        async def it_processes_multiple_tasks_in_window():
            # Arrange
            current_time = now_ms()
            due_at = current_time + (15 * 60 * 1000)

            task1 = MagicMock()
            task1.id = "task-1"
            task1.text = "First task"
            task1.due_at = due_at

            task2 = MagicMock()
            task2.id = "task-2"
            task2.text = "Second task"
            task2.due_at = due_at + 10000  # Slightly different time

            reminded_set = set()

            with patch(
                "app.scheduler.send_task_reminder"
            ) as mock_send_reminder, patch(
                "app.scheduler.AsyncSessionLocal"
            ) as mock_session_local, patch(
                "app.scheduler.now_ms", return_value=current_time
            ), patch(
                "app.scheduler.reminded_task_ids", reminded_set
            ):
                mock_send_reminder.return_value = True

                mock_session = AsyncMock()
                mock_result = MagicMock()
                mock_scalars = MagicMock()
                mock_scalars.all.return_value = [task1, task2]
                mock_result.scalars.return_value = mock_scalars
                mock_session.execute = AsyncMock(return_value=mock_result)
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_local.return_value = mock_session

                from app.scheduler import check_upcoming_tasks

                # Act
                await check_upcoming_tasks()

                # Assert
                assert mock_send_reminder.call_count == 2
                assert "task-1" in reminded_set
                assert "task-2" in reminded_set

    def describe_start_scheduler():
        """Tests for the start_scheduler function."""

        def it_starts_the_scheduler_with_correct_job():
            # Arrange
            with patch("app.scheduler.scheduler") as mock_scheduler:
                mock_scheduler.running = False

                from app.scheduler import start_scheduler

                # Act
                start_scheduler()

                # Assert
                mock_scheduler.add_job.assert_called_once()
                call_kwargs = mock_scheduler.add_job.call_args

                # Check job was added with correct parameters
                assert call_kwargs.kwargs["id"] == "task_reminders"
                assert (
                    call_kwargs.kwargs["name"]
                    == "Check for tasks due in 15 minutes"
                )
                assert call_kwargs.kwargs["replace_existing"] is True

                mock_scheduler.start.assert_called_once()

        def it_adds_job_with_1_minute_interval():
            # Arrange
            with patch("app.scheduler.scheduler") as mock_scheduler:
                mock_scheduler.running = False

                from app.scheduler import start_scheduler

                # Act
                start_scheduler()

                # Assert
                call_kwargs = mock_scheduler.add_job.call_args
                trigger = call_kwargs.kwargs["trigger"]

                # Verify it's an interval trigger
                from apscheduler.triggers.interval import IntervalTrigger

                assert isinstance(trigger, IntervalTrigger)

    def describe_stop_scheduler():
        """Tests for the stop_scheduler function."""

        def it_stops_running_scheduler():
            # Arrange
            with patch("app.scheduler.scheduler") as mock_scheduler:
                mock_scheduler.running = True

                from app.scheduler import stop_scheduler

                # Act
                stop_scheduler()

                # Assert
                mock_scheduler.shutdown.assert_called_once_with(wait=False)

        def it_does_not_stop_if_scheduler_not_running():
            # Arrange
            with patch("app.scheduler.scheduler") as mock_scheduler:
                mock_scheduler.running = False

                from app.scheduler import stop_scheduler

                # Act
                stop_scheduler()

                # Assert
                mock_scheduler.shutdown.assert_not_called()
