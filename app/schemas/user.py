"""
User Pydantic schemas for request/response validation.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8)
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class UserInDB(UserBase):
    """Schema for user stored in database (includes hashed password)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
