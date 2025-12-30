"""
User service layer.
Contains business logic for user CRUD operations.
"""
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination."""
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, user_in: UserCreate) -> User:
        """
        Create a new user.

        Note: In production, you should hash the password using a library like
        passlib or bcrypt. This is a simplified example.
        """
        # Check if email already exists
        existing = await self.get_by_email(user_in.email)
        if existing:
            raise ValueError(f"User with email {user_in.email} already exists")

        # In production, hash the password properly
        # Example: hashed_password = pwd_context.hash(user_in.password)
        hashed_password = f"hashed_{user_in.password}"  # Placeholder - use proper hashing!

        user = User(
            id=str(uuid4()),
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"Created user: {user.email}")
        return user

    async def update(self, user_id: str, user_in: UserUpdate) -> User | None:
        """Update an existing user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_in.model_dump(exclude_unset=True)

        # Handle password update
        if "password" in update_data:
            # In production, hash the password properly
            update_data["hashed_password"] = f"hashed_{update_data.pop('password')}"

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"Updated user: {user.email}")
        return user

    async def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.flush()

        logger.info(f"Deleted user: {user.email}")
        return True
