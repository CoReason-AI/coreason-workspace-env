import unittest
from unittest.mock import patch
import os

from src.core.tools.signer import sign_artifact, verify_artifact

class TestSigner(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Force the mock sigstore logic
        os.environ["MOCK_SIGSTORE"] = "1"
        
    def tearDown(self):
        if "MOCK_SIGSTORE" in os.environ:
            del os.environ["MOCK_SIGSTORE"]
            
    async def test_sign_artifact_mock(self):
        content = "print('hello world')"
        result = await sign_artifact(content)
        
        self.assertIn("signature", result)
        self.assertIn("certificate", result)
        self.assertEqual(result["signature"], "mock_sigstore_signature_bundle_v1")
        self.assertEqual(result["certificate"], "mock_sigstore_certificate_v1")
        
    async def test_verify_artifact_mock(self):
        content = "print('hello world')"
        is_valid = await verify_artifact(content, "mock_sigstore_signature_bundle_v1")
        self.assertTrue(is_valid)
        
        is_invalid = await verify_artifact(content, "bad_signature")
        self.assertFalse(is_invalid)
