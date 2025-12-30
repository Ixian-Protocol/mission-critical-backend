"""
Hello world controller.
Handles HTTP requests and coordinates with service layer.
"""
from fastapi import HTTPException, status
from typing import Dict, Any
import logging

from app.services.hello_service import HelloService
from app.core.exceptions import BadRequestException

logger = logging.getLogger(__name__)


class HelloController:
    """Controller for hello world endpoints."""

    def __init__(self):
        """Initialize controller with service dependencies."""
        self.hello_service = HelloService()

    async def get_hello(self, name: str | None = None) -> Dict[str, Any]:
        """
        Handle GET request for hello endpoint.

        Args:
            name: Optional name parameter from query string

        Returns:
            Response data from service layer

        Raises:
            BadRequestException: If name parameter is invalid
        """
        try:
            # Validate input if name is provided
            if name and len(name) > 100:
                raise BadRequestException("Name must be 100 characters or less")

            if name and not name.strip():
                raise BadRequestException("Name cannot be empty")

            # Call service layer
            result = self.hello_service.get_hello_message(name)

            logger.info(f"Successfully processed hello request for: {name or 'World'}")
            return result

        except BadRequestException:
            # Re-raise custom exceptions
            raise
        except Exception as e:
            # Log and wrap unexpected errors
            logger.error(f"Error in hello controller: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    async def get_health(self) -> Dict[str, Any]:
        """
        Handle GET request for health check endpoint.

        Returns:
            Health status from service layer
        """
        try:
            result = self.hello_service.get_health_status()
            return result
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy",
            )
