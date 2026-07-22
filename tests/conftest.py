import sys
import asyncio
import pytest
import os

# Test with tracing disabled to prevent test failures on missing credentials
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# Dummy env vars for pydantic-settings validation
dummy_envs = [
    "ENVIRONMENT", "ALLOWED_ORIGINS", "VAULT_ADDR", "VAULT_NAMESPACE",
    "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT",
    "REDIS_URL", "WORM_S3_BUCKET", "WORM_S3_REGION", "WORM_S3_ENDPOINT",
    "WORM_S3_ACCESS_KEY", "WORM_S3_SECRET_KEY", "OPENROUTER_API_KEY", "DIFY_API_KEY"
]
for env in dummy_envs:
    if env not in os.environ:
        if env == "POSTGRES_PORT":
            os.environ[env] = "5432"
        else:
            os.environ[env] = "test-dummy"

if sys.platform == 'win32':
    # Psycopg requires SelectorEventLoop on Windows for async mode
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Removed global_postgres_container fixture due to Zero Waste deprecation of custom DB 
# and to prevent testcontainers Docker crash.
