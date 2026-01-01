"""
Pydantic schemas for Tag API.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    """Base schema with common tag fields."""

    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., pattern=r"^#[0-9a-fA-F]{6}$")  # Hex color
    is_default: bool = False


class TagCreate(TagBase):
    """Schema for creating a new tag."""

    created_at: int  # Unix timestamp (ms) - client provides
    updated_at: int  # Unix timestamp (ms) - client provides


class TagUpdate(BaseModel):
    """Schema for updating an existing tag. All fields optional except updated_at."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    is_default: bool | None = None
    updated_at: int  # Unix timestamp (ms) - client provides


class TagResponse(TagBase):
    """Schema for tag responses including server-generated fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: int  # Unix timestamp (ms)
    updated_at: int  # Unix timestamp (ms)
    deleted_at: int | None = None
