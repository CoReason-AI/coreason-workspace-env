import os
import base64
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

class CloudKMSLicenseService:
    """
    Integrates with Hyperscaler Cloud KMS (AWS KMS, Azure Key Vault, GCP KMS)
    via Workload Identity / Instance Profiles to securely fetch the decryption key 
    in air-gapped VPCs via VPC Endpoints.
    """
    
    def __init__(self):
        self.kms_provider = os.environ.get("CLOUD_KMS_PROVIDER", "aws").lower()
        self.kms_key_id = os.environ.get("CLOUD_KMS_KEY_ID")
        
    def _fetch_key_aws(self) -> bytes:
        """Fetch the AES decryption key using AWS KMS and boto3."""
        try:
            import boto3
            # In an air-gapped environment with VPC Endpoints, boto3 automatically uses 
            # the attached IAM Role (Workload Identity) and routes through the VPC Endpoint.
            client = boto3.client('kms')
            # The actual implementation would decrypt a known ciphertext or fetch a parameter
            # For demonstration, we assume the key is stored in Secrets Manager or SSM
            # encrypted by the KMS key.
            ssm = boto3.client('ssm')
            response = ssm.get_parameter(
                Name=os.environ.get("KMS_SECRET_NAME", "/coreason/mcp/bundle_key"),
                WithDecryption=True
            )
            key_b64 = response['Parameter']['Value']
            return base64.b64decode(key_b64)
        except Exception as e:
            logger.error(f"Failed to fetch key from AWS KMS: {e}")
            raise

    def get_decryption_key(self) -> bytes:
        """
        Authenticates via Cloud IAM/Workload Identity and fetches the decryption key.
        """
        if not self.kms_key_id and not os.environ.get("KMS_SECRET_NAME"):
            # Fallback for local testing if explicitly allowed
            if os.environ.get("ALLOW_LOCAL_TEST_KEY", "false").lower() == "true":
                logger.warning("Using local test key from MCP_BUNDLE_KEY environment variable. DO NOT USE IN PRODUCTION.")
                key_b64 = os.environ.get("MCP_BUNDLE_KEY")
                if key_b64:
                    return base64.b64decode(key_b64)
            raise ValueError("KMS_SECRET_NAME or CLOUD_KMS_KEY_ID must be set for Cloud KMS integration.")
            
        if self.kms_provider == "aws":
            return self._fetch_key_aws()
        elif self.kms_provider == "azure":
            # Azure Key Vault integration would go here using azure-identity and azure-keyvault-secrets
            raise NotImplementedError("Azure Key Vault integration not yet implemented")
        elif self.kms_provider == "gcp":
            # GCP KMS integration would go here using google-cloud-kms
            raise NotImplementedError("GCP KMS integration not yet implemented")
        else:
            raise ValueError(f"Unsupported KMS provider: {self.kms_provider}")

    def decrypt_bundle(self, bundle_path: str) -> dict:
        """
        Reads the encrypted bundle, fetches the KMS key, and decrypts it strictly in-memory.
        Returns a dictionary of relative file paths to their YAML contents.
        """
        import json
        
        with open(bundle_path, 'rb') as f:
            final_data = f.read()
            
        nonce = final_data[:12]
        ciphertext = final_data[12:]
        
        key = self.get_decryption_key()
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
            
        aesgcm = AESGCM(key)
        
        try:
            payload = aesgcm.decrypt(nonce, ciphertext, None)
            bundle = json.loads(payload.decode('utf-8'))
            logger.info(f"Successfully decrypted bundle containing {len(bundle)} files in-memory.")
            return bundle
        except Exception as e:
            logger.error(f"Failed to decrypt MCP bundle: {e}")
            raise

license_service = CloudKMSLicenseService()
