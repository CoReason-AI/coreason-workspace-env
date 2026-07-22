import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class DifyDatasetConfig(BaseModel):
    dataset_id: str
    tenant_id: str
    api_url: str = Field(default="https://api.dify.ai/v1")
    
class DifyAdapter:
    """
    Adapter for integrating with Dify as a Headless Asset Manager.
    Adheres to the "Zero Waste" architecture by delegating RAG datasets,
    workspace isolation, and LLM secrets to Dify.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        from src.core.config import settings
        self.api_key = api_key or settings.DIFY_API_KEY
        self.base_url = (base_url or settings.DIFY_BASE_URL).rstrip('/')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def get_workspace_info(self) -> Dict[str, Any]:
        """
        Retrieves current workspace/tenant isolation info (Macro-RBAC).
        """
        response = await self.client.get("/info")
        response.raise_for_status()
        return response.json()

    async def get_provider_secrets(self, provider_name: str) -> Dict[str, Any]:
        """
        Retrieves LLM provider secrets from Dify's vault.
        Note: The actual Dify API for this might be internal or restricted.
        This provides the structural hook for the Meta-Agent Factory.
        """
        response = await self.client.get(f"/workspaces/current/providers/{provider_name}")
        response.raise_for_status()
        return response.json()

    async def query_dataset(self, dataset_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Queries a Dify RAG Vector Dataset. 
        This is intended to be exposed as a native `deepagents` tool.
        """
        # Using the Knowledge Base API endpoint for querying
        payload = {
            "query": query,
            "retrieval_model": {
                "top_k": top_k,
                "score_threshold": 0.5
            }
        }
        response = await self.client.post(f"/datasets/{dataset_id}/retrieve", json=payload)
        response.raise_for_status()
        return response.json().get("records", [])

    async def publish_app(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publishes a compiled deepagents configuration to the Dify App Portal.
        """
        response = await self.client.post("/apps", json=app_config)
        response.raise_for_status()
        return response.json()

    async def create_workspace(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Creates a new workspace/project via Dify API.
        """
        response = await self.client.post("/workspaces", json={"name": name, "description": description})
        response.raise_for_status()
        return response.json()

    async def delete_workspace(self, workspace_id: str) -> bool:
        """
        Deletes a workspace via Dify API.
        """
        response = await self.client.delete(f"/workspaces/{workspace_id}")
        response.raise_for_status()
        return True

    async def export_app(self, app_id: str) -> Dict[str, Any]:
        """
        Exports an app configuration from Dify.
        """
        response = await self.client.get(f"/apps/{app_id}/export")
        response.raise_for_status()
        return response.json()

    async def import_app(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Imports an app configuration to Dify.
        """
        response = await self.client.post("/apps/import", json=app_data)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
