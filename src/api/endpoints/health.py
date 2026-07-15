"""
REST API — Health endpoints.
Thin adapter over src.core.services.health_service.
"""
from fastapi import APIRouter

from src.core.services import health_service

router = APIRouter()


@router.get("/")
async def check_health():
    """Check platform health."""
    return await health_service.check()


@router.get("/version")
async def get_version():
    """Get platform version."""
    return health_service.get_version()
