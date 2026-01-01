"""
Tag API routes.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.controllers.tag_controller import TagController
from app.db.session import get_db
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get(
    "",
    response_model=list[TagResponse],
    summary="List tags",
    description="Get all tags. Use `since` parameter for sync to get only updated tags.",
)
async def get_tags(
    since: int | None = Query(
        None,
        description="Unix timestamp (ms). Returns only tags with updated_at > since",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[TagResponse]:
    """
    Get all tags, optionally filtered by update time.

    When `since` is provided, includes soft-deleted tags so clients can sync deletions.
    """
    controller = TagController(db)
    return await controller.get_tags(since=since)


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Get tag",
    description="Get a single tag by its ID.",
    responses={
        200: {"description": "Tag found"},
        404: {"description": "Tag not found"},
    },
)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Get a single tag by ID."""
    controller = TagController(db)
    return await controller.get_tag(str(tag_id))


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a new tag.",
    responses={
        201: {"description": "Tag created"},
        400: {"description": "Tag name already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Create a new tag."""
    controller = TagController(db)
    return await controller.create_tag(tag_in)


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update tag",
    description="Update an existing tag.",
    responses={
        200: {"description": "Tag updated"},
        400: {"description": "Tag name already exists"},
        404: {"description": "Tag not found"},
        422: {"description": "Validation error"},
    },
)
async def update_tag(
    tag_id: UUID,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Update an existing tag."""
    controller = TagController(db)
    return await controller.update_tag(str(tag_id), tag_in)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Soft-delete a tag. Cannot delete default tags.",
    responses={
        204: {"description": "Tag deleted"},
        400: {"description": "Cannot delete default tags"},
        404: {"description": "Tag not found"},
    },
)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a tag."""
    controller = TagController(db)
    await controller.delete_tag(str(tag_id))
