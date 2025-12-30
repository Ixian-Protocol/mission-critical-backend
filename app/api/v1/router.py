"""
API v1 main router.
Aggregates all v1 route modules.
"""
from fastapi import APIRouter

from app.api.v1.routes import hello_routes, user_routes

# Create the main v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(hello_routes.router)
api_router.include_router(user_routes.router)

# Add more routers here as you build out your API
# api_router.include_router(items_routes.router)
