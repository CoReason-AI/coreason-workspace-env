import os
import logging
import tempfile
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)

async def sign_artifact(content: str) -> Dict[str, str]:
    """
    Cryptographically signs the artifact using Sigstore.
    This acts as the Proof of Valid Validation (PVV).
    """
    logger.info("Signing artifact to generate Proof of Valid Validation (PVV)...")
    
    # If we are in a headless CI/CD test environment without OIDC, bypass real network calls.
    if os.environ.get("OPENAI_API_KEY") == "test_mock_key" or os.environ.get("MOCK_SIGSTORE") == "1":
        return {
            "signature": "mock_sigstore_signature_bundle_v1",
            "certificate": "mock_sigstore_certificate_v1"
        }
    
    # Real SDK/CLI integration
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
        tf.write(content)
        temp_path = tf.name
        
    bundle_path = f"{temp_path}.sigstore"
    
    try:
        # Run sigstore sign command
        # sigstore sign <file> --bundle <bundle_file>
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "sigstore", "sign", temp_path, "--bundle", bundle_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Sigstore signing failed: {stderr.decode()}")
            raise RuntimeError("Failed to cryptographically sign artifact.")
            
        with open(bundle_path, 'r') as f:
            bundle_content = f.read()
            
        return {
            "signature": bundle_content, # The complete bundle acts as the signature and certificate
            "certificate": "embedded_in_bundle"
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(bundle_path):
            os.remove(bundle_path)

async def verify_artifact(content: str, signature: str, certificate: str = "") -> bool:
    """
    Verifies a Sigstore signature for a given artifact.
    """
    if os.environ.get("OPENAI_API_KEY") == "test_mock_key" or os.environ.get("MOCK_SIGSTORE") == "1":
        return signature == "mock_sigstore_signature_bundle_v1"

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
        tf.write(content)
        temp_path = tf.name
        
    bundle_path = f"{temp_path}.sigstore"
    with open(bundle_path, 'w') as bf:
        bf.write(signature)
        
    try:
        # verify command requires a policy or identity check, but for basic check we can run it
        # sigstore verify github --cert-identity <identity> <file> --bundle <bundle>
        # To avoid strict identity checking during local tests, we just assume a generic verification
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "sigstore", "verify", "github", "--cert-identity", "https://github.com/CoReason-AI/coreason-workspace-env/.github/workflows/ci.yml@refs/heads/main", temp_path, "--bundle", bundle_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode == 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(bundle_path):
            os.remove(bundle_path)
