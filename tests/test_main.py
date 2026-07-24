import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app

@pytest.mark.asyncio
async def test_main_app_health_endpoint():
    """
    E2E No Mock Test: Ensure the FastAPI application initializes correctly
    and the integrated health endpoint returns 200 OK.
    """
    # Use ASGITransport to bypass the actual network for faster E2E tests,
    # but still execute the full FastAPI lifecycle and routing layer.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ok", "healthy", "degraded"]
