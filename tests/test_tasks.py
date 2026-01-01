"""
Tests for the Task API endpoints.

Uses pytest-describe for BDD-style test organization.
"""
import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.models.task import Task, now_ms


def describe_tasks_api():
    """Tests for /api/v1/tasks endpoints."""

    def describe_create_task():
        """POST /api/v1/tasks endpoint tests."""

        @pytest.mark.asyncio
        async def it_creates_a_task_with_valid_data(
            client: AsyncClient, sample_task_data: dict[str, Any]
        ):
            # Act
            response = await client.post("/api/v1/tasks", json=sample_task_data)

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["text"] == sample_task_data["text"]
            assert data["description"] == sample_task_data["description"]
            assert data["completed"] == sample_task_data["completed"]
            assert data["important"] == sample_task_data["important"]
            assert data["tag"] == sample_task_data["tag"]
            assert "id" in data
            assert "created_at" in data
            assert "updated_at" in data
            assert data["deleted_at"] is None

        @pytest.mark.asyncio
        async def it_creates_a_task_with_minimal_data(client: AsyncClient):
            # Arrange - only required field is text
            task_data = {"text": "Minimal task"}

            # Act
            response = await client.post("/api/v1/tasks", json=task_data)

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["text"] == "Minimal task"
            assert data["description"] == ""
            assert data["completed"] is False
            assert data["important"] is False
            assert data["tag"] == "General"
            assert data["recurrence"] == "none"

        @pytest.mark.asyncio
        async def it_creates_a_task_with_all_tags(client: AsyncClient):
            # Test each valid tag
            tags = ["General", "Work", "Personal", "Research", "Design"]

            for tag in tags:
                # Act
                response = await client.post(
                    "/api/v1/tasks",
                    json={"text": f"Task with {tag} tag", "tag": tag}
                )

                # Assert
                assert response.status_code == 201
                assert response.json()["tag"] == tag

        @pytest.mark.asyncio
        async def it_creates_a_task_with_recurrence(client: AsyncClient):
            # Test each recurrence type
            recurrences = ["none", "daily", "weekly", "monthly"]

            for recurrence in recurrences:
                # Act
                response = await client.post(
                    "/api/v1/tasks",
                    json={
                        "text": f"Task with {recurrence} recurrence",
                        "recurrence": recurrence
                    }
                )

                # Assert
                assert response.status_code == 201
                assert response.json()["recurrence"] == recurrence

        @pytest.mark.asyncio
        async def it_creates_a_task_with_due_date(client: AsyncClient):
            # Arrange
            due_at = now_ms() + 86400000  # Tomorrow

            # Act
            response = await client.post(
                "/api/v1/tasks",
                json={"text": "Task with due date", "due_at": due_at}
            )

            # Assert
            assert response.status_code == 201
            assert response.json()["due_at"] == due_at

        @pytest.mark.asyncio
        async def it_returns_422_for_empty_text(client: AsyncClient):
            # Act
            response = await client.post("/api/v1/tasks", json={"text": ""})

            # Assert
            assert response.status_code == 422
            data = response.json()
            # API uses custom error structure with "error" key
            assert "error" in data
            assert data["error"]["type"] == "ValidationError"

        @pytest.mark.asyncio
        async def it_returns_422_for_missing_text(client: AsyncClient):
            # Act
            response = await client.post("/api/v1/tasks", json={})

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_text_too_long(client: AsyncClient):
            # Arrange - text max length is 500
            long_text = "a" * 501

            # Act
            response = await client.post("/api/v1/tasks", json={"text": long_text})

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_accepts_custom_tag_names(client: AsyncClient):
            # Tags are now dynamic - any string up to 50 chars is valid
            # Act
            response = await client.post(
                "/api/v1/tasks",
                json={"text": "Task", "tag": "CustomTag"}
            )

            # Assert
            assert response.status_code == 201
            assert response.json()["tag"] == "CustomTag"

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_recurrence(client: AsyncClient):
            # Act
            response = await client.post(
                "/api/v1/tasks",
                json={"text": "Task", "recurrence": "yearly"}
            )

            # Assert
            assert response.status_code == 422

    def describe_get_tasks():
        """GET /api/v1/tasks endpoint tests."""

        @pytest.mark.asyncio
        async def it_returns_empty_list_when_no_tasks_exist(client: AsyncClient):
            # Act
            response = await client.get("/api/v1/tasks")

            # Assert
            assert response.status_code == 200
            assert response.json() == []

        @pytest.mark.asyncio
        async def it_returns_all_non_deleted_tasks(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act
            response = await client.get("/api/v1/tasks")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(multiple_tasks)

        @pytest.mark.asyncio
        async def it_excludes_soft_deleted_tasks(
            client: AsyncClient,
            existing_task: Task,
            deleted_task: Task,
        ):
            # Act
            response = await client.get("/api/v1/tasks")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == existing_task.id

        @pytest.mark.asyncio
        async def it_filters_by_tag(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act
            response = await client.get("/api/v1/tasks", params={"tag": "Work"})

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            for task in data:
                assert task["tag"] == "Work"

        @pytest.mark.asyncio
        async def it_filters_by_completed(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act - get completed tasks
            response = await client.get("/api/v1/tasks", params={"completed": True})

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["completed"] is True

        @pytest.mark.asyncio
        async def it_filters_by_not_completed(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act - get incomplete tasks
            response = await client.get("/api/v1/tasks", params={"completed": False})

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            for task in data:
                assert task["completed"] is False

        @pytest.mark.asyncio
        async def it_filters_by_important(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act
            response = await client.get("/api/v1/tasks", params={"important": True})

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            for task in data:
                assert task["important"] is True

        @pytest.mark.asyncio
        async def it_combines_multiple_filters(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act - get incomplete, important tasks
            response = await client.get(
                "/api/v1/tasks",
                params={"completed": False, "important": True}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            for task in data:
                assert task["completed"] is False
                assert task["important"] is True

        @pytest.mark.asyncio
        async def it_returns_empty_when_no_tasks_match_filter(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Act - no Design tasks exist
            response = await client.get("/api/v1/tasks", params={"tag": "Design"})

            # Assert
            assert response.status_code == 200
            assert response.json() == []

    def describe_get_task():
        """GET /api/v1/tasks/{id} endpoint tests."""

        @pytest.mark.asyncio
        async def it_returns_task_by_id(
            client: AsyncClient, existing_task: Task
        ):
            # Act
            response = await client.get(f"/api/v1/tasks/{existing_task.id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == existing_task.id
            assert data["text"] == existing_task.text
            assert data["description"] == existing_task.description

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_task(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.get(f"/api/v1/tasks/{nonexistent_id}")

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_uuid(client: AsyncClient):
            # Act
            response = await client.get("/api/v1/tasks/not-a-uuid")

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_can_retrieve_soft_deleted_task(
            client: AsyncClient, deleted_task: Task
        ):
            # Note: get_task does not filter by deleted_at, so deleted tasks
            # can still be retrieved by ID
            # Act
            response = await client.get(f"/api/v1/tasks/{deleted_task.id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == deleted_task.id
            assert data["deleted_at"] is not None

    def describe_update_task():
        """PATCH /api/v1/tasks/{id} endpoint tests."""

        @pytest.mark.asyncio
        async def it_updates_task_text(
            client: AsyncClient, existing_task: Task
        ):
            # Act
            response = await client.patch(
                f"/api/v1/tasks/{existing_task.id}",
                json={"text": "Updated text"}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "Updated text"
            assert data["description"] == existing_task.description  # Unchanged

        @pytest.mark.asyncio
        async def it_updates_multiple_fields(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange
            update_data = {
                "text": "New text",
                "description": "New description",
                "completed": True,
                "important": True,
                "tag": "Work",
            }

            # Act
            response = await client.patch(
                f"/api/v1/tasks/{existing_task.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["text"] == "New text"
            assert data["description"] == "New description"
            assert data["completed"] is True
            assert data["important"] is True
            assert data["tag"] == "Work"

        @pytest.mark.asyncio
        async def it_updates_updated_at_timestamp(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange
            original_updated_at = existing_task.updated_at

            # Act
            response = await client.patch(
                f"/api/v1/tasks/{existing_task.id}",
                json={"text": "Updated"}
            )

            # Assert
            assert response.status_code == 200
            assert response.json()["updated_at"] > original_updated_at

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_task(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.patch(
                f"/api/v1/tasks/{nonexistent_id}",
                json={"text": "Updated"}
            )

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_422_for_empty_text(
            client: AsyncClient, existing_task: Task
        ):
            # Act
            response = await client.patch(
                f"/api/v1/tasks/{existing_task.id}",
                json={"text": ""}
            )

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_accepts_custom_tag_on_update(
            client: AsyncClient, existing_task: Task
        ):
            # Tags are now dynamic - any string up to 50 chars is valid
            # Act
            response = await client.patch(
                f"/api/v1/tasks/{existing_task.id}",
                json={"tag": "CustomTag"}
            )

            # Assert
            assert response.status_code == 200
            assert response.json()["tag"] == "CustomTag"

        @pytest.mark.asyncio
        async def it_allows_empty_update(
            client: AsyncClient, existing_task: Task
        ):
            # Act - sending empty update is valid (no changes)
            response = await client.patch(
                f"/api/v1/tasks/{existing_task.id}",
                json={}
            )

            # Assert
            assert response.status_code == 200

    def describe_delete_task():
        """DELETE /api/v1/tasks/{id} (soft delete) endpoint tests."""

        @pytest.mark.asyncio
        async def it_soft_deletes_task(
            client: AsyncClient, existing_task: Task
        ):
            # Act
            response = await client.delete(f"/api/v1/tasks/{existing_task.id}")

            # Assert
            assert response.status_code == 204

            # Verify task is soft-deleted (still retrievable but has deleted_at)
            get_response = await client.get(f"/api/v1/tasks/{existing_task.id}")
            assert get_response.status_code == 200
            assert get_response.json()["deleted_at"] is not None

        @pytest.mark.asyncio
        async def it_excludes_soft_deleted_from_list(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange - soft delete the task
            await client.delete(f"/api/v1/tasks/{existing_task.id}")

            # Act
            response = await client.get("/api/v1/tasks")

            # Assert - task should not appear in list
            assert response.status_code == 200
            assert response.json() == []

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_task(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.delete(f"/api/v1/tasks/{nonexistent_id}")

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_uuid(client: AsyncClient):
            # Act
            response = await client.delete("/api/v1/tasks/not-a-uuid")

            # Assert
            assert response.status_code == 422

    def describe_hard_delete_task():
        """DELETE /api/v1/tasks/{id}/hard endpoint tests."""

        @pytest.mark.asyncio
        async def it_permanently_deletes_task(
            client: AsyncClient, existing_task: Task
        ):
            # Act
            response = await client.delete(f"/api/v1/tasks/{existing_task.id}/hard")

            # Assert
            assert response.status_code == 204

            # Verify task is completely gone
            get_response = await client.get(f"/api/v1/tasks/{existing_task.id}")
            assert get_response.status_code == 404

        @pytest.mark.asyncio
        async def it_can_hard_delete_soft_deleted_task(
            client: AsyncClient, deleted_task: Task
        ):
            # Act
            response = await client.delete(f"/api/v1/tasks/{deleted_task.id}/hard")

            # Assert
            assert response.status_code == 204

            # Verify task is completely gone
            get_response = await client.get(f"/api/v1/tasks/{deleted_task.id}")
            assert get_response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_task(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.delete(f"/api/v1/tasks/{nonexistent_id}/hard")

            # Assert
            assert response.status_code == 404


def describe_sync_api():
    """Tests for /api/v1/sync endpoint."""

    def describe_sync_tasks():
        """POST /api/v1/sync endpoint tests."""

        @pytest.mark.asyncio
        async def it_returns_server_time_on_empty_sync(client: AsyncClient):
            # Arrange
            sync_request = {"tasks": [], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "server_time" in data
            assert isinstance(data["server_time"], int)
            assert data["tasks"] == []
            assert data["deleted_ids"] == []

        @pytest.mark.asyncio
        async def it_returns_all_tasks_on_first_sync(
            client: AsyncClient, multiple_tasks: list[Task]
        ):
            # Arrange - first sync (no last_sync_at)
            sync_request = {"tasks": [], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data["tasks"]) == len(multiple_tasks)

        @pytest.mark.asyncio
        async def it_inserts_new_task_from_client(client: AsyncClient):
            # Arrange
            task_id = str(uuid.uuid4())
            current_time = now_ms()
            client_task = {
                "id": task_id,
                "text": "New client task",
                "description": "Created on client",
                "completed": False,
                "important": False,
                "tag": "General",
                "due_at": None,
                "recurrence": "none",
                "recurrence_alt": False,
                "created_at": current_time,
                "updated_at": current_time,
                "deleted_at": None,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200

            # Verify task was created on server
            get_response = await client.get(f"/api/v1/tasks/{task_id}")
            assert get_response.status_code == 200
            assert get_response.json()["text"] == "New client task"

        @pytest.mark.asyncio
        async def it_updates_server_task_when_client_is_newer(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange - client has newer version
            client_updated_at = existing_task.updated_at + 10000
            client_task = {
                "id": existing_task.id,
                "text": "Updated by client",
                "description": "Client made changes",
                "completed": True,
                "important": True,
                "tag": "Work",
                "due_at": None,
                "recurrence": "none",
                "recurrence_alt": False,
                "created_at": existing_task.created_at,
                "updated_at": client_updated_at,
                "deleted_at": None,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200

            # Verify task was updated on server
            get_response = await client.get(f"/api/v1/tasks/{existing_task.id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["text"] == "Updated by client"
            assert data["completed"] is True
            assert data["important"] is True
            assert data["tag"] == "Work"

        @pytest.mark.asyncio
        async def it_skips_update_when_server_is_newer(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange - client has older version
            client_updated_at = existing_task.updated_at - 10000
            client_task = {
                "id": existing_task.id,
                "text": "Old client version",
                "description": "Stale data",
                "completed": True,
                "important": True,
                "tag": "Work",
                "due_at": None,
                "recurrence": "none",
                "recurrence_alt": False,
                "created_at": existing_task.created_at,
                "updated_at": client_updated_at,
                "deleted_at": None,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200

            # Verify server task was NOT updated (server wins)
            get_response = await client.get(f"/api/v1/tasks/{existing_task.id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["text"] == existing_task.text  # Original value
            assert data["completed"] is False  # Original value

        @pytest.mark.asyncio
        async def it_syncs_deleted_at_from_client(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange - client marks task as deleted
            current_time = now_ms()
            client_task = {
                "id": existing_task.id,
                "text": existing_task.text,
                "description": existing_task.description,
                "completed": existing_task.completed,
                "important": existing_task.important,
                "tag": existing_task.tag,
                "due_at": existing_task.due_at,
                "recurrence": existing_task.recurrence,
                "recurrence_alt": existing_task.recurrence_alt,
                "created_at": existing_task.created_at,
                "updated_at": current_time,
                "deleted_at": current_time,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200

            # Verify task is now soft-deleted on server
            get_response = await client.get(f"/api/v1/tasks/{existing_task.id}")
            assert get_response.status_code == 200
            assert get_response.json()["deleted_at"] is not None

        @pytest.mark.asyncio
        async def it_returns_tasks_modified_since_last_sync(
            client: AsyncClient, existing_task: Task
        ):
            # Arrange - set last_sync_at to before task was created
            last_sync_at = existing_task.updated_at - 10000

            sync_request = {"tasks": [], "last_sync_at": last_sync_at}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["id"] == existing_task.id

        @pytest.mark.asyncio
        async def it_excludes_recently_synced_tasks_from_response(
            client: AsyncClient,
        ):
            # Arrange - client sends a task, it should not be returned
            task_id = str(uuid.uuid4())
            current_time = now_ms()
            client_task = {
                "id": task_id,
                "text": "Just synced task",
                "description": "",
                "completed": False,
                "important": False,
                "tag": "General",
                "due_at": None,
                "recurrence": "none",
                "recurrence_alt": False,
                "created_at": current_time,
                "updated_at": current_time,
                "deleted_at": None,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert - the task we just sent should NOT be in the response
            assert response.status_code == 200
            data = response.json()
            returned_ids = [t["id"] for t in data["tasks"]]
            assert task_id not in returned_ids

        @pytest.mark.asyncio
        async def it_handles_multiple_tasks_in_sync(client: AsyncClient):
            # Arrange - multiple new tasks from client
            current_time = now_ms()
            tasks = [
                {
                    "id": str(uuid.uuid4()),
                    "text": f"Sync task {i}",
                    "description": "",
                    "completed": False,
                    "important": False,
                    "tag": "General",
                    "due_at": None,
                    "recurrence": "none",
                    "recurrence_alt": False,
                    "created_at": current_time + i,
                    "updated_at": current_time + i,
                    "deleted_at": None,
                }
                for i in range(5)
            ]
            sync_request = {"tasks": tasks, "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200

            # Verify all tasks were created
            list_response = await client.get("/api/v1/tasks")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 5

        @pytest.mark.asyncio
        async def it_accepts_custom_tag_in_sync(client: AsyncClient):
            # Tags are now dynamic - any string up to 50 chars is valid
            task_id = str(uuid.uuid4())
            client_task = {
                "id": task_id,
                "text": "Task",
                "description": "",
                "completed": False,
                "important": False,
                "tag": "CustomTag",  # Custom tag is now valid
                "due_at": None,
                "recurrence": "none",
                "recurrence_alt": False,
                "created_at": now_ms(),
                "updated_at": now_ms(),
                "deleted_at": None,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 200

            # Verify task was created with custom tag
            get_response = await client.get(f"/api/v1/tasks/{task_id}")
            assert get_response.status_code == 200
            assert get_response.json()["tag"] == "CustomTag"

        @pytest.mark.asyncio
        async def it_returns_422_for_missing_required_fields(client: AsyncClient):
            # Arrange - task missing id
            client_task = {
                "text": "Task without ID",
                "description": "",
                "completed": False,
                "important": False,
                "tag": "General",
                "due_at": None,
                "recurrence": "none",
                "recurrence_alt": False,
                "created_at": now_ms(),
                "updated_at": now_ms(),
                "deleted_at": None,
            }
            sync_request = {"tasks": [client_task], "last_sync_at": None}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_includes_deleted_tasks_in_sync_response(
            client: AsyncClient, deleted_task: Task
        ):
            # Arrange - last sync before task was deleted
            last_sync_at = deleted_task.updated_at - 10000

            sync_request = {"tasks": [], "last_sync_at": last_sync_at}

            # Act
            response = await client.post("/api/v1/sync", json=sync_request)

            # Assert - deleted task should be included so client can update
            assert response.status_code == 200
            data = response.json()
            task_ids = [t["id"] for t in data["tasks"]]
            assert deleted_task.id in task_ids

            # Verify deleted_at is included
            deleted_in_response = next(
                t for t in data["tasks"] if t["id"] == deleted_task.id
            )
            assert deleted_in_response["deleted_at"] is not None
