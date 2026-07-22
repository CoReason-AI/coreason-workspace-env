import unittest
import os
import asyncio


class TestCoreCompute(unittest.IsolatedAsyncioTestCase):
    def test_strict_ssot_config_missing_vars(self):
        """Test Rule 8: Missing environment variables must raise ValidationError."""
        from src.core.config import Settings
        from pydantic import ValidationError
        
        # Save current environment
        original_env = dict(os.environ)
        os.environ.clear()
        
        try:
            with self.assertRaises(ValidationError):
                # Ensure it attempts to read from empty environment and fails on missing required fields
                Settings(_env_file=None)
        finally:
            # Restore environment
            os.environ.update(original_env)

if __name__ == '__main__':
    unittest.main()
