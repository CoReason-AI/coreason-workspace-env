import os
import hashlib
import json
import logging
from testcontainers.postgres import PostgresContainer
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
        # Check if settings are injected
        from src.core.config import settings
        if not settings.POSTGRES_HOST or settings.POSTGRES_HOST == "localhost" and settings.POSTGRES_USER == "":
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

