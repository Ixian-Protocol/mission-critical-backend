"""
Hello world service layer.
Contains business logic for hello world functionality.
"""
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class HelloService:
    """Service class for hello world operations."""

    def get_hello_message(self, name: str | None = None) -> Dict[str, Any]:
        """
        Generate a hello world message.

        Args:
            name: Optional name to personalize the greeting

        Returns:
            Dictionary containing the greeting and metadata
        """
        logger.info(f"Generating hello message for: {name or 'World'}")

        greeting = f"Hello, {name}!" if name else "Hello, World!"

        return {
            "message": greeting,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "hello_service",
            "version": "1.0.0",
        }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the service.

        Returns:
            Dictionary containing health status information
        """
        logger.debug("Health check requested")

        return {
            "status": "healthy",
            "service": "hello_service",
            "timestamp": datetime.utcnow().isoformat(),
        }
