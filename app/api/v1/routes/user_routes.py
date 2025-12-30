"""
User routes.
Defines the API endpoints for user CRUD operations.
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.controllers.user_controller import UserController
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Get all users",
    description="Retrieve all users with optional pagination",
    responses={
        200: {"description": "List of users"},
        500: {"description": "Internal server error"},
    },
)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """Get all users with pagination."""
    controller = UserController(db)
    return await controller.get_users(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID",
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_user(
    user_id: str = Path(..., description="The user ID"),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get a specific user by ID."""
    controller = UserController(db)
    return await controller.get_user(user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user",
    description="Create a new user with the provided data",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Bad request - validation error or email already exists"},
        500: {"description": "Internal server error"},
    },
)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user."""
    controller = UserController(db)
    return await controller.create_user(user_in)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    description="Update an existing user with the provided data",
    responses={
        200: {"description": "User updated successfully"},
        400: {"description": "Bad request - validation error"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_user(
    user_id: str = Path(..., description="The user ID"),
    user_in: UserUpdate = ...,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update an existing user."""
    controller = UserController(db)
    return await controller.update_user(user_id, user_in)


@router.delete(
    "/{user_id}",
    summary="Delete a user",
    description="Delete a user by their ID",
    responses={
        200: {"description": "User deleted successfully"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_user(
    user_id: str = Path(..., description="The user ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a user."""
    controller = UserController(db)
    return await controller.delete_user(user_id)
