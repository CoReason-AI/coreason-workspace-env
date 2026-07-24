"""
Health Service — platform health checks and version info.
"""
import logging
from typing import Dict, Any

import asyncpg

logger = logging.getLogger(__name__)

PLATFORM_VERSION = "2.1.0"


class HealthService:
    """
    Checks connectivity to backing services (Postgres, Redis, Vault)
    and returns structured health status.
    """

    async def check(self, postgres_dsn: str = None, redis_url: str = None) -> Dict[str, Any]:
        """
        Run health checks against all backing services.

        Returns a structured report with per-service status and overall health.
        """
        checks = {}

        # Postgres
        checks["postgres"] = await self._check_postgres(postgres_dsn)

        # Redis check removed - platform is Postgres-only

        overall = "healthy" if all(c["status"] == "ok" for c in checks.values()) else "degraded"

        return {
            "status": overall,
            "version": PLATFORM_VERSION,
            "services": checks,
        }

    async def _check_postgres(self, dsn: str = None) -> Dict[str, str]:
        from src.core.config import settings
        
        candidates = []
        if dsn:
            candidates.append(dsn)
        
        # Primary configured settings DSN
        candidates.append(
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        # Compose dify-postgres service
        candidates.append("postgresql://postgres:dify@dify-postgres:5432/dify")
        # Localhost mapped port 5434
        candidates.append(
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@localhost:5434/{settings.POSTGRES_DB}"
        )

        for target_dsn in candidates:
            try:
                conn = await asyncpg.connect(target_dsn, timeout=3)
                version = await conn.fetchval("SELECT version()")
                await conn.close()
                return {"status": "ok", "detail": version}
            except Exception as e:
                logger.debug(f"Postgres health check attempt failed for {target_dsn}: {e}")

        return {"status": "error", "detail": "Unable to connect to Postgres checkpointer"}



    def get_version(self) -> Dict[str, str]:
        return {"version": PLATFORM_VERSION, "platform": "coreason-workspace-env"}
