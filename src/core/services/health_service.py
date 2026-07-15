"""
Health Service — platform health checks and version info.
"""
import logging
from typing import Dict, Any

import asyncpg
import redis.asyncio as aioredis

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

        # Redis
        checks["redis"] = await self._check_redis(redis_url)

        overall = "healthy" if all(c["status"] == "ok" for c in checks.values()) else "degraded"

        return {
            "status": overall,
            "version": PLATFORM_VERSION,
            "services": checks,
        }

    async def _check_postgres(self, dsn: str = None) -> Dict[str, str]:
        if not dsn:
            try:
                from src.core.config import settings
                dsn = (
                    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
                    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
                )
            except Exception:
                return {"status": "unknown", "detail": "Settings unavailable"}

        try:
            conn = await asyncpg.connect(dsn, timeout=5)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            return {"status": "ok", "detail": version}
        except Exception as e:
            logger.warning(f"Postgres health check failed: {e}")
            return {"status": "error", "detail": str(e)}

    async def _check_redis(self, url: str = None) -> Dict[str, str]:
        if not url:
            try:
                from src.core.config import settings
                url = settings.REDIS_URL
            except Exception:
                return {"status": "unknown", "detail": "Settings unavailable"}

        try:
            client = aioredis.from_url(url, decode_responses=True)
            pong = await client.ping()
            await client.aclose()
            return {"status": "ok", "detail": f"PONG={pong}"}
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {"status": "error", "detail": str(e)}

    def get_version(self) -> Dict[str, str]:
        return {"version": PLATFORM_VERSION, "platform": "coreason-workspace-env"}
