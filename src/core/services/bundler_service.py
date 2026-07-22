import os
import json
import base64
import logging
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.core.services.license_service import license_service

logger = logging.getLogger(__name__)

class BundlerService:
    """
    Manages the bundling, encryption, and decryption of MCP agent YAML manifests.
    """
    
    def bundle_agents(self, source_dir: str, output_file: str, key_b64: str):
        """
        Walks the source directory, collects YAML files, and encrypts them into a single bundle.
        """
        source_path = Path(source_dir)
        if not key_b64:
            raise ValueError("Key must be provided for bundling")
            
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
            
        aesgcm = AESGCM(key)
        
        bundle = {}
        for root, _, files in os.walk(source_path):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(source_path).as_posix()
                    with open(file_path, 'r', encoding='utf-8') as f:
                        bundle[relative_path] = f.read()
                        
        payload = json.dumps(bundle).encode('utf-8')
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, payload, None)
        
        # Store nonce + ciphertext together
        final_data = nonce + ciphertext
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'wb') as f:
            f.write(final_data)
            
        logger.info(f"Successfully bundled {len(bundle)} agents into {output_file}")
        return len(bundle)

    def decrypt_bundle(self, bundle_path: str) -> dict:
        """
        Reads the encrypted bundle, fetches the KMS key from license_service, 
        and decrypts it strictly in-memory.
        Returns a dictionary of relative file paths to their YAML contents.
        """
        with open(bundle_path, 'rb') as f:
            final_data = f.read()
            
        nonce = final_data[:12]
        ciphertext = final_data[12:]
        
        key = license_service.get_decryption_key()
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

    def synthesize_project_template(
        self,
        project_id: str,
        name: str,
        description: str,
        orchestrator_yaml: str,
        tools: list = None,
        skills: list = None,
    ) -> dict:
        """
        Synthesizes a self-similar agentic application template.
        Copies the platform's runtime harness, mounts the orchestrator YAML,
        registers a PEN 66197 URN, and returns the project structure.
        """
        from src.core.ontology import CoreasonURN
        from src.core.services.catalog_service import catalog_service

        urn_obj = CoreasonURN(resource_type="project", resource_id=project_id)
        oid_urn = urn_obj.to_oid_urn()
        coreason_url = urn_obj.to_coreason_url()

        # Register synthesized template in PEN 66197 Catalog
        catalog_entry = catalog_service.register_entry(
            urn=oid_urn,
            name=name,
            description=description,
            resource_type="project",
            tags=["synthesized", "self_similar", "template"],
            metadata={
                "tools": tools or [],
                "skills": skills or [],
                "coreason_url": coreason_url,
            },
            source_code=orchestrator_yaml,
        )

        logger.info(f"Synthesized self-similar project template {oid_urn} ({name})")
        return {
            "status": "success",
            "project_id": project_id,
            "urn": oid_urn,
            "coreason_url": coreason_url,
            "catalog_entry": catalog_entry.model_dump(),
        }

bundler_service = BundlerService()
