import os
import hashlib
import json
import logging
# from testcontainers.postgres import PostgresContainer
# from testcontainers.minio import MinioContainer
import unittest
from typing import Any

logger = logging.getLogger(__name__)

class ZeroMockTestCase(unittest.IsolatedAsyncioTestCase):
    """
    Advanced Testing Framework (Zero Mocks).
    Provisions ephemeral real infrastructure using Testcontainers.
    """
    postgres = None
    
    @classmethod
    def setUpClass(cls):
        logger.info("Relying on global Postgres container from conftest.py...")
        from src.core.config import settings
        pg_host = getattr(settings, "POSTGRES_HOST", None)
        pg_user = getattr(settings, "POSTGRES_USER", None)
        if not pg_host or pg_host == "localhost" and pg_user == "":
            logger.warning("Postgres settings appear unset. Zero Mock tests may fail if global fixture didn't run.")
        
    @classmethod
    def tearDownClass(cls):
        pass

    def assertPydanticValid(self, data: Any, schema_class):
        """Deterministic Python assertions for Pydantic output validation."""
        try:
            if isinstance(data, str):
                obj = schema_class.model_validate_json(data)
            else:
                obj = schema_class.model_validate(data)
            self.assertIsNotNone(obj)
        except Exception as e:
            self.fail(f"Pydantic validation failed: {e}")

