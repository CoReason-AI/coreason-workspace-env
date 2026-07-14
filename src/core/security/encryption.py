import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class HSMEncryptionWrapper:
    """
    BYOK & HSM Encryption Wrapper for Postgres and S3.
    Enforces CISO-grade encryption at rest using Customer-Managed Keys.
    In a true production environment, this interfaces with an external HSM (AWS KMS/Azure Key Vault).
    For the platform baseline, it enforces Fernet symmetric encryption using an HSM-injected root key.
    """
    def __init__(self):
        # The HSM_ROOT_KEY must be injected by the OIDC Vault Federation at runtime.
        # Strict SSOT: No fallback defaults.
        self._hsm_key = os.environ["HSM_ROOT_KEY"]
        self._salt = os.environ.get("HSM_SALT", "ciso_default_salt_do_not_use_in_prod").encode()
        
        # Derive a secure Fernet key from the HSM root key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._hsm_key.encode()))
        self._fernet = Fernet(key)
        logger.info("HSM Encryption Wrapper initialized securely.")

    def encrypt_postgres_payload(self, data: str) -> bytes:
        """Encrypts sensitive LangGraph state before persisting to Postgres."""
        return self._fernet.encrypt(data.encode())

    def decrypt_postgres_payload(self, encrypted_data: bytes) -> str:
        """Decrypts LangGraph state retrieved from Postgres."""
        return self._fernet.decrypt(encrypted_data).decode()

    def encrypt_s3_object(self, file_bytes: bytes) -> bytes:
        """Encrypts Virtual Filesystem (VFS) or WORM Audit logs before uploading to S3."""
        return self._fernet.encrypt(file_bytes)

    def decrypt_s3_object(self, encrypted_bytes: bytes) -> bytes:
        """Decrypts Virtual Filesystem (VFS) or WORM Audit logs retrieved from S3."""
        return self._fernet.decrypt(encrypted_bytes)

# Singleton instance to be injected into database and S3 clients
hsm_crypto = None

def get_crypto_wrapper() -> HSMEncryptionWrapper:
    global hsm_crypto
    if not hsm_crypto:
        hsm_crypto = HSMEncryptionWrapper()
    return hsm_crypto
