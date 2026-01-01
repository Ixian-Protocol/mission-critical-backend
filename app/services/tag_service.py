"""
Tag service for CRUD operations.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.task import now_ms
from app.schemas.tag import TagCreate, TagUpdate


class TagService:
    """Service for tag CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tag_id: str) -> Tag | None:
        """Get a tag by ID."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Tag | None:
        """Get a tag by name."""
        result = await self.db.execute(select(Tag).where(Tag.name == name))
        return result.scalar_one_or_none()

    async def get_all(self, include_deleted: bool = False) -> list[Tag]:
        """
        Get all tags.

        Args:
            include_deleted: If True, include soft-deleted tags
        """
        query = select(Tag)

        if not include_deleted:
            query = query.where(Tag.deleted_at.is_(None))

        query = query.order_by(Tag.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_since(self, since: int) -> list[Tag]:
        """
        Get tags updated since a given timestamp.

        Includes soft-deleted tags so clients can sync deletions.
        """
        query = select(Tag).where(Tag.updated_at > since).order_by(Tag.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, tag_in: TagCreate) -> Tag:
        """Create a new tag."""
        tag = Tag(
            name=tag_in.name,
            color=tag_in.color,
            is_default=tag_in.is_default,
            created_at=tag_in.created_at,
            updated_at=tag_in.updated_at,
        )
        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)
        return tag

    async def update(self, tag_id: str, tag_in: TagUpdate) -> Tag | None:
        """
        Update an existing tag.

        Returns None if tag not found.
        """
        tag = await self.get_by_id(tag_id)
        if tag is None:
            return None

        update_data = tag_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tag, field, value)

        await self.db.flush()
        await self.db.refresh(tag)
        return tag

    async def soft_delete(self, tag_id: str) -> bool:
        """
        Soft delete a tag by setting deleted_at.

        Returns True if tag was deleted, False if not found.
        """
        tag = await self.get_by_id(tag_id)
        if tag is None:
            return False

        tag.deleted_at = now_ms()
        tag.updated_at = now_ms()
        await self.db.flush()
        return True
