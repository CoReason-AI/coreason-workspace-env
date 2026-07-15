import os
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VaultFederationClient:
    """
    OIDC/SPIFFE Vault Federation for Identity Management.
    Enforces CISO requirement: The platform MUST NOT store secrets.
    It uses Kubernetes Service Accounts (OIDC/SPIFFE) to federate identity directly with Enterprise Vaults.
    """
    def __init__(self):
        # Strict SSOT: Keys must exist in environment.
        self.vault_addr = os.environ["VAULT_ADDR"]
        self.vault_namespace = os.environ["VAULT_NAMESPACE"]
        self.kubernetes_jwt_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        
        self.vault_token = None
        self._authenticate()

    def _authenticate(self):
        """
        Authenticates with HashiCorp Vault using the Kubernetes Service Account OIDC JWT.
        """
        if not os.path.exists(self.kubernetes_jwt_path):
            logger.warning("Kubernetes JWT not found. Running in local dev mode?")
            # Fallback for local development if allowed by strict CISO policies.
            # In true production, this would fail fast.
            if os.environ.get("ENVIRONMENT") == "local":
                token = os.environ.get("LOCAL_VAULT_TOKEN")
                if not token:
                    raise ValueError("LOCAL_VAULT_TOKEN environment variable is required in local dev mode.")
                self.vault_token = token
                return
            else:
                raise FileNotFoundError("Kubernetes OIDC JWT not found. Cannot federate with Vault.")
                
        with open(self.kubernetes_jwt_path, "r") as f:
            jwt = f.read().strip()
            
        # Example HashiCorp Vault Kubernetes Auth implementation
        auth_url = f"{self.vault_addr}/v1/auth/kubernetes/login"
        payload = {"jwt": jwt, "role": "coreason-platform-role"}
        headers = {"X-Vault-Namespace": self.vault_namespace}
        
        try:
            response = requests.post(auth_url, json=payload, headers=headers)
            response.raise_for_status()
            self.vault_token = response.json()["auth"]["client_token"]
            logger.info("Successfully federated identity with Enterprise Vault via OIDC.")
        except Exception as e:
            logger.error(f"Failed to federate identity with Vault: {str(e)}")
            raise

    def get_secret(self, secret_path: str) -> Dict[str, Any]:
        """
        Retrieves a secret dynamically from the Enterprise Vault.
        This is used for JIT Impersonation and dynamic API key retrieval.
        """
        if not self.vault_token:
            raise ValueError("Vault client is not authenticated.")
            
        url = f"{self.vault_addr}/v1/{secret_path}"
        headers = {
            "X-Vault-Token": self.vault_token,
            "X-Vault-Namespace": self.vault_namespace
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["data"]["data"]

# Singleton instance
vault_client = None

def get_vault_client() -> VaultFederationClient:
    global vault_client
    if not vault_client:
        vault_client = VaultFederationClient()
    return vault_client
