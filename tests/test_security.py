import unittest
import os
import json
from src.core.security.audit import WORMStorageAuditor
from src.core.security.proxy_delegation import ProxyDelegationLoop
from src.core.security.encryption import HSMEncryptionWrapper
from src.core.security.vault import VaultFederationClient

class TestSecurityIdentity(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # We assume the framework passes dummy config
        os.environ["WORM_S3_BUCKET"] = "test-bucket"
        os.environ["WORM_S3_REGION"] = "us-east-1"
        os.environ["HSM_ROOT_KEY"] = "dummy-root-key"
        os.environ["VAULT_ADDR"] = "http://127.0.0.1:8200"
        os.environ["VAULT_NAMESPACE"] = "coreason-admin"
        os.environ["ENVIRONMENT"] = "local"
        
        self.auditor = WORMStorageAuditor()
        self.proxy_loop = ProxyDelegationLoop()
        self.encryption = HSMEncryptionWrapper()
        self.vault = VaultFederationClient()

    def test_worm_storage_auditor_hashing(self):
        """Assert that SHA-256 event hashing is structurally valid."""
        event = {"action": "destructive_write", "agent_id": "agent-123"}
        
        # Test hash generation
        log_hash = self.auditor._hash_event(event)
        self.assertEqual(len(log_hash), 64) # SHA-256 hex digest length
        
        # Ensure determinism
        event2 = {"action": "destructive_write", "agent_id": "agent-123"}
        self.assertEqual(self.auditor._hash_event(event), self.auditor._hash_event(event2))
        
        # Ensure difference
        event3 = {"action": "destructive_write", "agent_id": "agent-456"}
        self.assertNotEqual(self.auditor._hash_event(event), self.auditor._hash_event(event3))

    async def test_proxy_delegation_loop(self):
        """Test JIT approval request queuing and resolution logic."""
        request_id = await self.proxy_loop.request_jit_execution(
            agent_id="agent-007",
            action="drop_database",
            payload={"db": "test"}
        )
        from src.core.security.auth import UserIdentity
        mock_user = UserIdentity(
            user_id="u123",
            email="supervisor@coreason.ai",
            roles=["supervisor"],
            session_id="s123"
        )
        await self.proxy_loop.approve_jit_execution(request_id, mock_user)
        # Ensure it moved to executed state
        self.assertEqual(self.proxy_loop.pending_requests[request_id]["status"], "executed")

    def test_vault_oidc_provider(self):
        """Test SPIFFE/OIDC token exchange payload generation."""
        # Check that it pulled the mock local token
        self.assertEqual(self.vault.vault_token, "mock_local_token")

    def test_byok_encryption_wrapper(self):
        """Test AES-GCM data encryption/decryption cycles."""
        plaintext = "secret_project_data"
        
        # Test postgres payload encryption
        encrypted = self.encryption.encrypt_postgres_payload(plaintext)
        self.assertNotEqual(encrypted, plaintext.encode())
        
        decrypted = self.encryption.decrypt_postgres_payload(encrypted)
        self.assertEqual(decrypted, plaintext)

if __name__ == '__main__':
    unittest.main()
