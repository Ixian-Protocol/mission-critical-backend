"""
Hello world routes.
Defines the API endpoints and their OpenAPI documentation.
"""
from fastapi import APIRouter, Query
from typing import Dict, Any

from app.api.v1.controllers.hello_controller import HelloController

router = APIRouter(prefix="/hello", tags=["Hello"])

# Initialize controller
hello_controller = HelloController()


@router.get(
    "",
    response_model=Dict[str, Any],
    summary="Get hello message",
    description="Returns a hello world message, optionally personalized with a name",
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Hello, World!",
                        "timestamp": "2025-01-15T12:00:00.000000",
                        "service": "hello_service",
                        "version": "1.0.0",
                    }
                }
            },
        },
        400: {"description": "Bad request - invalid name parameter"},
        500: {"description": "Internal server error"},
    },
)
async def get_hello(
    name: str | None = Query(
        None,
        description="Name to personalize the greeting",
        max_length=100,
        example="Alice",
    )
) -> Dict[str, Any]:
    """
    Get a hello world message.

    This endpoint demonstrates the basic structure of the API with
    controller-service architecture.
    """
    return await hello_controller.get_hello(name)


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health check",
    description="Check if the hello service is healthy",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "hello_service",
                        "timestamp": "2025-01-15T12:00:00.000000",
                    }
                }
            },
        },
        503: {"description": "Service unavailable"},
    },
)
async def get_health() -> Dict[str, Any]:
    """
    Health check endpoint for the hello service.
    """
    return await hello_controller.get_health()
