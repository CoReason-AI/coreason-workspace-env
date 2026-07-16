import sys
import asyncio
import pytest
import os

os.environ["LANGFUSE_ENABLED"] = "false"

try:
    from src.core.tracing.config import langfuse_config
    langfuse_config.enabled = False
except ImportError:
    pass

if sys.platform == 'win32':
    # Psycopg requires SelectorEventLoop on Windows for async mode
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture(scope="session", autouse=True)
def global_postgres_container():
    """Spin up a single Postgres container for the entire test session."""
    from testcontainers.postgres import PostgresContainer
    from src.core.config import settings
    
    postgres = PostgresContainer("postgres:15-alpine")
    postgres.start()
    
    # Override global settings
    settings.POSTGRES_USER = postgres.username
    settings.POSTGRES_PASSWORD = postgres.password
    settings.POSTGRES_HOST = postgres.get_container_host_ip()
    settings.POSTGRES_PORT = int(postgres.get_exposed_port(5432))
    settings.POSTGRES_DB = postgres.dbname
    
    yield postgres
    
    postgres.stop()
