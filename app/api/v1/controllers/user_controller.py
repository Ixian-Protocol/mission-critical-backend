"""
User controller.
Handles HTTP requests and coordinates with service layer.
"""
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.exceptions import NotFoundException, BadRequestException

logger = logging.getLogger(__name__)


class UserController:
    """Controller for user endpoints."""

    def __init__(self, db: AsyncSession):
        """Initialize controller with database session."""
        self.user_service = UserService(db)

    async def get_users(self, skip: int = 0, limit: int = 100) -> list[UserResponse]:
        """Get all users with pagination."""
        try:
            users = await self.user_service.get_all(skip=skip, limit=limit)
            return [UserResponse.model_validate(user) for user in users]
        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    async def get_user(self, user_id: str) -> UserResponse:
        """Get a user by ID."""
        try:
            user = await self.user_service.get_by_id(user_id)
            if not user:
                raise NotFoundException(f"User with id {user_id} not found")
            return UserResponse.model_validate(user)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    async def create_user(self, user_in: UserCreate) -> UserResponse:
        """Create a new user."""
        try:
            user = await self.user_service.create(user_in)
            logger.info(f"Created user: {user.email}")
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise BadRequestException(str(e))
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    async def update_user(self, user_id: str, user_in: UserUpdate) -> UserResponse:
        """Update an existing user."""
        try:
            user = await self.user_service.update(user_id, user_in)
            if not user:
                raise NotFoundException(f"User with id {user_id} not found")
            logger.info(f"Updated user: {user.email}")
            return UserResponse.model_validate(user)
        except NotFoundException:
            raise
        except ValueError as e:
            raise BadRequestException(str(e))
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    async def delete_user(self, user_id: str) -> dict:
        """Delete a user."""
        try:
            deleted = await self.user_service.delete(user_id)
            if not deleted:
                raise NotFoundException(f"User with id {user_id} not found")
            logger.info(f"Deleted user: {user_id}")
            return {"message": "User deleted successfully"}
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )
