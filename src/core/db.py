import asyncpg
from typing import Optional
from src.core.config import settings

_global_pool: Optional[asyncpg.Pool] = None

async def get_db_pool() -> asyncpg.Pool:
    """
    Lazily creates and returns a global asyncpg connection pool.
    Constructs the DSN strictly from validated environment settings to enforce Rule 8.
    """
    global _global_pool
    if _global_pool is None:
        dsn = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        _global_pool = await asyncpg.create_pool(dsn, min_size=1, max_size=20)
    return _global_pool
