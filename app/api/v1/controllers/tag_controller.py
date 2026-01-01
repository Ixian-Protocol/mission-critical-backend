"""
Tag controller for handling HTTP requests.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import TagService

logger = logging.getLogger(__name__)


class TagController:
    """Controller for tag-related operations."""

    def __init__(self, db: AsyncSession):
        self.service = TagService(db)

    async def get_tags(self, since: int | None = None) -> list[TagResponse]:
        """Get all tags, optionally filtered by updated_at."""
        if since is not None:
            tags = await self.service.get_since(since)
        else:
            tags = await self.service.get_all()
        return [TagResponse.model_validate(tag) for tag in tags]

    async def get_tag(self, tag_id: str) -> TagResponse:
        """Get a single tag by ID."""
        tag = await self.service.get_by_id(tag_id)
        if tag is None:
            raise NotFoundException(f"Tag with id '{tag_id}' not found")
        return TagResponse.model_validate(tag)

    async def create_tag(self, tag_in: TagCreate) -> TagResponse:
        """Create a new tag."""
        # Check for duplicate name
        existing = await self.service.get_by_name(tag_in.name)
        if existing and existing.deleted_at is None:
            raise BadRequestException(f"Tag '{tag_in.name}' already exists")

        tag = await self.service.create(tag_in)
        return TagResponse.model_validate(tag)

    async def update_tag(self, tag_id: str, tag_in: TagUpdate) -> TagResponse:
        """Update an existing tag."""
        # Check tag exists
        existing = await self.service.get_by_id(tag_id)
        if existing is None:
            raise NotFoundException(f"Tag with id '{tag_id}' not found")

        # Check for duplicate name if name is being changed
        if tag_in.name and tag_in.name != existing.name:
            name_check = await self.service.get_by_name(tag_in.name)
            if name_check and name_check.deleted_at is None:
                raise BadRequestException(f"Tag '{tag_in.name}' already exists")

        tag = await self.service.update(tag_id, tag_in)
        return TagResponse.model_validate(tag)

    async def delete_tag(self, tag_id: str) -> None:
        """Soft delete a tag."""
        # Check tag exists
        existing = await self.service.get_by_id(tag_id)
        if existing is None:
            raise NotFoundException(f"Tag with id '{tag_id}' not found")

        # Cannot delete default tags
        if existing.is_default:
            raise BadRequestException("Cannot delete default tags")

        await self.service.soft_delete(tag_id)
