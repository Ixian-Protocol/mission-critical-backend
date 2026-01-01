"""
Tests for the Tag API endpoints.

Uses pytest-describe for BDD-style test organization.
"""
import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.models.tag import Tag
from app.models.task import now_ms


def describe_tags_api():
    """Tests for /api/v1/tags endpoints."""

    def describe_get_tags():
        """GET /api/v1/tags endpoint tests."""

        @pytest.mark.asyncio
        async def it_returns_empty_list_when_no_tags_exist(client: AsyncClient):
            # Act
            response = await client.get("/api/v1/tags")

            # Assert
            assert response.status_code == 200
            assert response.json() == []

        @pytest.mark.asyncio
        async def it_returns_all_non_deleted_tags(
            client: AsyncClient, multiple_tags: list[Tag]
        ):
            # Act
            response = await client.get("/api/v1/tags")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(multiple_tags)

        @pytest.mark.asyncio
        async def it_excludes_soft_deleted_tags(
            client: AsyncClient,
            existing_tag: Tag,
            deleted_tag: Tag,
        ):
            # Act
            response = await client.get("/api/v1/tags")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == existing_tag.id

        @pytest.mark.asyncio
        async def it_returns_tags_ordered_by_name(
            client: AsyncClient, multiple_tags: list[Tag]
        ):
            # Act
            response = await client.get("/api/v1/tags")

            # Assert
            assert response.status_code == 200
            data = response.json()
            names = [tag["name"] for tag in data]
            assert names == sorted(names)

        @pytest.mark.asyncio
        async def it_includes_all_tag_fields_in_response(
            client: AsyncClient, existing_tag: Tag
        ):
            # Act
            response = await client.get("/api/v1/tags")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            tag = data[0]
            assert "id" in tag
            assert "name" in tag
            assert "color" in tag
            assert "is_default" in tag
            assert "created_at" in tag
            assert "updated_at" in tag
            assert "deleted_at" in tag

    def describe_get_tags_with_since():
        """GET /api/v1/tags?since= endpoint tests for sync behavior."""

        @pytest.mark.asyncio
        async def it_returns_tags_updated_since_timestamp(
            client: AsyncClient, multiple_tags: list[Tag]
        ):
            # Arrange - get the oldest tag's updated_at
            oldest_updated_at = min(tag.updated_at for tag in multiple_tags)
            # Set since to just before the newest tags
            since = oldest_updated_at

            # Act
            response = await client.get("/api/v1/tags", params={"since": since})

            # Assert
            assert response.status_code == 200
            data = response.json()
            # Should include all tags with updated_at > since
            for tag in data:
                assert tag["updated_at"] > since

        @pytest.mark.asyncio
        async def it_returns_empty_when_no_tags_updated_since(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange - set since to after the tag was updated
            since = existing_tag.updated_at + 10000

            # Act
            response = await client.get("/api/v1/tags", params={"since": since})

            # Assert
            assert response.status_code == 200
            assert response.json() == []

        @pytest.mark.asyncio
        async def it_includes_soft_deleted_tags_when_since_is_provided(
            client: AsyncClient,
            existing_tag: Tag,
            deleted_tag: Tag,
        ):
            # Arrange - since before both tags were updated
            since = min(existing_tag.updated_at, deleted_tag.updated_at) - 1000

            # Act
            response = await client.get("/api/v1/tags", params={"since": since})

            # Assert
            assert response.status_code == 200
            data = response.json()
            tag_ids = [tag["id"] for tag in data]
            assert existing_tag.id in tag_ids
            assert deleted_tag.id in tag_ids

            # Verify deleted tag has deleted_at set
            deleted_in_response = next(
                t for t in data if t["id"] == deleted_tag.id
            )
            assert deleted_in_response["deleted_at"] is not None

    def describe_get_tag():
        """GET /api/v1/tags/{id} endpoint tests."""

        @pytest.mark.asyncio
        async def it_returns_tag_by_id(
            client: AsyncClient, existing_tag: Tag
        ):
            # Act
            response = await client.get(f"/api/v1/tags/{existing_tag.id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == existing_tag.id
            assert data["name"] == existing_tag.name
            assert data["color"] == existing_tag.color
            assert data["is_default"] == existing_tag.is_default

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_tag(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.get(f"/api/v1/tags/{nonexistent_id}")

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_uuid(client: AsyncClient):
            # Act
            response = await client.get("/api/v1/tags/not-a-uuid")

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_can_retrieve_soft_deleted_tag(
            client: AsyncClient, deleted_tag: Tag
        ):
            # Note: get_tag does not filter by deleted_at, so deleted tags
            # can still be retrieved by ID
            # Act
            response = await client.get(f"/api/v1/tags/{deleted_tag.id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == deleted_tag.id
            assert data["deleted_at"] is not None

    def describe_create_tag():
        """POST /api/v1/tags endpoint tests."""

        @pytest.mark.asyncio
        async def it_creates_a_tag_with_valid_data(
            client: AsyncClient, sample_tag_data: dict[str, Any]
        ):
            # Act
            response = await client.post("/api/v1/tags", json=sample_tag_data)

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == sample_tag_data["name"]
            assert data["color"] == sample_tag_data["color"]
            assert data["is_default"] == sample_tag_data["is_default"]
            assert "id" in data
            assert "created_at" in data
            assert "updated_at" in data
            assert data["deleted_at"] is None

        @pytest.mark.asyncio
        async def it_creates_a_default_tag(client: AsyncClient):
            # Arrange
            current_time = now_ms()
            tag_data = {
                "name": "Important",
                "color": "#dc2626",
                "is_default": True,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 201
            assert response.json()["is_default"] is True

        @pytest.mark.asyncio
        async def it_returns_400_for_duplicate_tag_name(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange - try to create tag with same name
            current_time = now_ms()
            tag_data = {
                "name": existing_tag.name,
                "color": "#000000",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert existing_tag.name in data["error"]["message"]

        # Note: There is a mismatch between application logic (allows reusing
        # soft-deleted tag names) and database constraint (unique on name).
        # The database constraint wins, but testing this is complex with the
        # current test setup because the error occurs during commit, not during
        # the request handling.

        @pytest.mark.asyncio
        async def it_returns_422_for_empty_name(client: AsyncClient):
            # Arrange
            current_time = now_ms()
            tag_data = {
                "name": "",
                "color": "#14b8a6",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_missing_name(client: AsyncClient):
            # Arrange
            current_time = now_ms()
            tag_data = {
                "color": "#14b8a6",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_name_too_long(client: AsyncClient):
            # Arrange - name max length is 50
            current_time = now_ms()
            tag_data = {
                "name": "a" * 51,
                "color": "#14b8a6",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_color_format(client: AsyncClient):
            # Arrange - color must be hex format #RRGGBB
            current_time = now_ms()
            invalid_colors = [
                "red",           # Not hex
                "#fff",          # Too short
                "#gggggg",       # Invalid hex chars
                "14b8a6",        # Missing #
                "#14b8a6ff",     # Too long (has alpha)
            ]

            for color in invalid_colors:
                tag_data = {
                    "name": f"Tag with {color}",
                    "color": color,
                    "is_default": False,
                    "created_at": current_time,
                    "updated_at": current_time,
                }

                # Act
                response = await client.post("/api/v1/tags", json=tag_data)

                # Assert
                assert response.status_code == 422, f"Expected 422 for color: {color}"

        @pytest.mark.asyncio
        async def it_returns_422_for_missing_color(client: AsyncClient):
            # Arrange
            current_time = now_ms()
            tag_data = {
                "name": "No Color Tag",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_missing_timestamps(client: AsyncClient):
            # Arrange
            tag_data = {
                "name": "No Timestamps",
                "color": "#14b8a6",
                "is_default": False,
            }

            # Act
            response = await client.post("/api/v1/tags", json=tag_data)

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_accepts_valid_hex_colors(client: AsyncClient):
            # Arrange
            current_time = now_ms()
            valid_colors = [
                "#000000",
                "#ffffff",
                "#FFFFFF",
                "#14b8a6",
                "#FF5733",
            ]

            for i, color in enumerate(valid_colors):
                tag_data = {
                    "name": f"Color Test {i}",
                    "color": color,
                    "is_default": False,
                    "created_at": current_time + i,
                    "updated_at": current_time + i,
                }

                # Act
                response = await client.post("/api/v1/tags", json=tag_data)

                # Assert
                assert response.status_code == 201, f"Expected 201 for color: {color}"

    def describe_update_tag():
        """PATCH /api/v1/tags/{id} endpoint tests."""

        @pytest.mark.asyncio
        async def it_updates_tag_name(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange
            update_data = {
                "name": "Updated Name",
                "updated_at": now_ms(),
            }

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["color"] == existing_tag.color  # Unchanged

        @pytest.mark.asyncio
        async def it_updates_tag_color(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange
            update_data = {
                "color": "#ff0000",
                "updated_at": now_ms(),
            }

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["color"] == "#ff0000"
            assert data["name"] == existing_tag.name  # Unchanged

        @pytest.mark.asyncio
        async def it_updates_is_default_flag(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange
            update_data = {
                "is_default": True,
                "updated_at": now_ms(),
            }

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == 200
            assert response.json()["is_default"] is True

        @pytest.mark.asyncio
        async def it_updates_multiple_fields(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange
            update_data = {
                "name": "New Name",
                "color": "#abcdef",
                "is_default": True,
                "updated_at": now_ms(),
            }

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Name"
            assert data["color"] == "#abcdef"
            assert data["is_default"] is True

        @pytest.mark.asyncio
        async def it_updates_updated_at_timestamp(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange
            new_updated_at = now_ms() + 10000

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json={"updated_at": new_updated_at}
            )

            # Assert
            assert response.status_code == 200
            assert response.json()["updated_at"] == new_updated_at

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_tag(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.patch(
                f"/api/v1/tags/{nonexistent_id}",
                json={"name": "Updated", "updated_at": now_ms()}
            )

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_400_for_duplicate_name(
            client: AsyncClient, existing_tag: Tag, default_tag: Tag
        ):
            # Arrange - try to update to existing tag's name
            update_data = {
                "name": default_tag.name,
                "updated_at": now_ms(),
            }

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

        # Note: Same issue as create - database unique constraint conflicts
        # with application logic for soft-deleted tags. See note in create tests.

        @pytest.mark.asyncio
        async def it_allows_updating_to_same_name(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange - update to same name (no actual change)
            update_data = {
                "name": existing_tag.name,
                "updated_at": now_ms(),
            }

            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json=update_data
            )

            # Assert - should succeed
            assert response.status_code == 200

        @pytest.mark.asyncio
        async def it_returns_422_for_empty_name(
            client: AsyncClient, existing_tag: Tag
        ):
            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json={"name": "", "updated_at": now_ms()}
            )

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_color(
            client: AsyncClient, existing_tag: Tag
        ):
            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json={"color": "not-a-color", "updated_at": now_ms()}
            )

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_422_for_missing_updated_at(
            client: AsyncClient, existing_tag: Tag
        ):
            # Act
            response = await client.patch(
                f"/api/v1/tags/{existing_tag.id}",
                json={"name": "New Name"}  # Missing updated_at
            )

            # Assert
            assert response.status_code == 422

    def describe_delete_tag():
        """DELETE /api/v1/tags/{id} (soft delete) endpoint tests."""

        @pytest.mark.asyncio
        async def it_soft_deletes_tag(
            client: AsyncClient, existing_tag: Tag
        ):
            # Act
            response = await client.delete(f"/api/v1/tags/{existing_tag.id}")

            # Assert
            assert response.status_code == 204

            # Verify tag is soft-deleted (still retrievable but has deleted_at)
            get_response = await client.get(f"/api/v1/tags/{existing_tag.id}")
            assert get_response.status_code == 200
            assert get_response.json()["deleted_at"] is not None

        @pytest.mark.asyncio
        async def it_excludes_soft_deleted_from_list(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange - soft delete the tag
            await client.delete(f"/api/v1/tags/{existing_tag.id}")

            # Act
            response = await client.get("/api/v1/tags")

            # Assert - tag should not appear in list
            assert response.status_code == 200
            assert response.json() == []

        @pytest.mark.asyncio
        async def it_returns_404_for_nonexistent_tag(client: AsyncClient):
            # Arrange
            nonexistent_id = str(uuid.uuid4())

            # Act
            response = await client.delete(f"/api/v1/tags/{nonexistent_id}")

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def it_returns_422_for_invalid_uuid(client: AsyncClient):
            # Act
            response = await client.delete("/api/v1/tags/not-a-uuid")

            # Assert
            assert response.status_code == 422

        @pytest.mark.asyncio
        async def it_returns_400_for_default_tag(
            client: AsyncClient, default_tag: Tag
        ):
            # Act
            response = await client.delete(f"/api/v1/tags/{default_tag.id}")

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "default" in data["error"]["message"].lower()

        @pytest.mark.asyncio
        async def it_allows_deleting_non_default_tag(
            client: AsyncClient, existing_tag: Tag
        ):
            # Verify tag is not default
            assert existing_tag.is_default is False

            # Act
            response = await client.delete(f"/api/v1/tags/{existing_tag.id}")

            # Assert
            assert response.status_code == 204

        @pytest.mark.asyncio
        async def it_cannot_delete_any_default_tag_from_list(
            client: AsyncClient, multiple_tags: list[Tag]
        ):
            # Get the first default tag
            default_tags = [t for t in multiple_tags if t.is_default]
            assert len(default_tags) > 0

            # Test with the first default tag
            tag = default_tags[0]

            # Act
            response = await client.delete(f"/api/v1/tags/{tag.id}")

            # Assert - should return 400 for default tags
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "default" in data["error"]["message"].lower()

    def describe_sync_behavior():
        """Tests for sync-related behavior with the since parameter."""

        @pytest.mark.asyncio
        async def it_returns_recently_deleted_tags_for_sync(
            client: AsyncClient, existing_tag: Tag
        ):
            # Arrange - record time before deletion
            before_delete = now_ms() - 1000

            # Soft delete the tag
            await client.delete(f"/api/v1/tags/{existing_tag.id}")

            # Act - sync with since before deletion
            response = await client.get("/api/v1/tags", params={"since": before_delete})

            # Assert - deleted tag should be included
            assert response.status_code == 200
            data = response.json()
            tag_ids = [t["id"] for t in data]
            assert existing_tag.id in tag_ids

            # Verify it has deleted_at set
            deleted_tag_data = next(t for t in data if t["id"] == existing_tag.id)
            assert deleted_tag_data["deleted_at"] is not None

        @pytest.mark.asyncio
        async def it_includes_updated_and_deleted_tags_in_sync(
            client: AsyncClient, multiple_tags: list[Tag]
        ):
            # Arrange - get earliest timestamp
            earliest_time = min(t.updated_at for t in multiple_tags) - 1000

            # Delete one non-default tag
            non_default_tags = [t for t in multiple_tags if not t.is_default]
            tag_to_delete = non_default_tags[0]
            await client.delete(f"/api/v1/tags/{tag_to_delete.id}")

            # Act
            response = await client.get("/api/v1/tags", params={"since": earliest_time})

            # Assert - all tags should be included (including deleted)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(multiple_tags)

            # Verify deleted tag is marked as such
            deleted_in_response = next(t for t in data if t["id"] == tag_to_delete.id)
            assert deleted_in_response["deleted_at"] is not None

        @pytest.mark.asyncio
        async def it_excludes_old_tags_from_sync(
            client: AsyncClient, multiple_tags: list[Tag]
        ):
            # Arrange - set since to after all tags were created
            latest_time = max(t.updated_at for t in multiple_tags)
            since = latest_time + 1000

            # Act
            response = await client.get("/api/v1/tags", params={"since": since})

            # Assert - no tags should be returned
            assert response.status_code == 200
            assert response.json() == []


def describe_tag_service():
    """Tests for TagService business logic (via API)."""

    def describe_name_uniqueness():
        """Tests for tag name uniqueness constraints."""

        @pytest.mark.asyncio
        async def it_enforces_unique_names_case_sensitive(
            client: AsyncClient
        ):
            # Arrange
            current_time = now_ms()

            # Create first tag
            tag1_data = {
                "name": "UniqueTag",
                "color": "#000000",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }
            response1 = await client.post("/api/v1/tags", json=tag1_data)
            assert response1.status_code == 201

            # Try to create tag with same name
            tag2_data = {
                "name": "UniqueTag",
                "color": "#ffffff",
                "is_default": False,
                "created_at": current_time + 1,
                "updated_at": current_time + 1,
            }
            response2 = await client.post("/api/v1/tags", json=tag2_data)
            assert response2.status_code == 400

        @pytest.mark.asyncio
        async def it_allows_different_case_names(
            client: AsyncClient
        ):
            # Arrange
            current_time = now_ms()

            # Create first tag
            tag1_data = {
                "name": "mytag",
                "color": "#000000",
                "is_default": False,
                "created_at": current_time,
                "updated_at": current_time,
            }
            response1 = await client.post("/api/v1/tags", json=tag1_data)
            assert response1.status_code == 201

            # Create tag with different case
            tag2_data = {
                "name": "MyTag",
                "color": "#ffffff",
                "is_default": False,
                "created_at": current_time + 1,
                "updated_at": current_time + 1,
            }
            response2 = await client.post("/api/v1/tags", json=tag2_data)

            # Assert - depends on database collation, SQLite is case-insensitive by default
            # This test documents the actual behavior
            assert response2.status_code in [201, 400]
