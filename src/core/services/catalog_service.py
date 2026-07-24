import time
import logging
from typing import Dict, Any, List, Optional
from src.core.ontology import CoreasonURN, CatalogEntry

logger = logging.getLogger(__name__)


class CatalogService:
    """
    URN Authority & Project Catalog Service.
    Powered by Coreason AI's IANA Private Enterprise Number (66197).
    Enables past project search, architecture review, and modular component import.
    """

    def __init__(self):
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._seed_default_catalog()

    def _seed_default_catalog(self):
        """Seeds built-in core exemplars into the catalog."""
        default_projects = [
            {
                "resource_type": "project",
                "resource_id": "epistemic_analyst_v1",
                "name": "Epistemic Analyst Pipeline",
                "description": "Multi-agent causal inference & hypothesis generation pipeline with DoWhy integration.",
                "tags": ["causal_inference", "hypothesis", "dowhy", "epistemic"],
                "metadata": {"entrypoint": "research_agent", "topology": "dag"},
            },
            {
                "resource_type": "project",
                "resource_id": "mcp_gateway_factory",
                "name": "MCP Gateway Factory",
                "description": "Opinionated agent factory platform transpiling YAML definitions to LangGraph nodes.",
                "tags": ["mcp", "factory", "langgraph", "deepagents"],
                "metadata": {"entrypoint": "factory_ceo", "topology": "swarm"},
            },
            {
                "resource_type": "agent",
                "resource_id": "yaml_compiler_agent",
                "name": "YAML Compiler Agent",
                "description": "Deterministic sub-agent compiling prompt specifications into validated agent.yaml manifests.",
                "tags": ["compiler", "subagent", "yaml", "generator"],
                "metadata": {"skills": ["building/agent_building_standards.md"]},
            },
        ]
        for p in default_projects:
            urn_obj = CoreasonURN(resource_type=p["resource_type"], resource_id=p["resource_id"])
            self.register_entry(
                urn=urn_obj.to_oid_urn(),
                name=p["name"],
                description=p["description"],
                resource_type=p["resource_type"],
                tags=p["tags"],
                metadata=p["metadata"],
            )

    def register_entry(
        self,
        urn: str,
        name: str,
        description: str,
        resource_type: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None,
    ) -> CatalogEntry:
        """Registers a project or component in the catalog under a PEN 66197 URN or Coreason URL."""
        parsed_urn = CoreasonURN.parse(urn)
        canonical_oid = parsed_urn.to_oid_urn()
        canonical_url = parsed_urn.to_coreason_url()

        entry = CatalogEntry(
            urn=canonical_oid,
            name=name,
            description=description,
            resource_type=resource_type,
            version=version,
            tags=tags or [],
            metadata={**(metadata or {}), "coreason_url": canonical_url, "pen": 66197},
            source_code=source_code,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        self._entries[canonical_oid] = entry.model_dump()
        self._entries[canonical_url] = entry.model_dump()
        logger.info(f"Registered catalog entry {canonical_oid} ({canonical_url})")
        return entry

    def resolve_urn(self, urn_str: str) -> Optional[Dict[str, Any]]:
        """Resolves an OID URN or Coreason URL to its catalog entry."""
        try:
            parsed = CoreasonURN.parse(urn_str)
            return self._entries.get(parsed.to_oid_urn()) or self._entries.get(parsed.to_coreason_url())
        except Exception as e:
            logger.warning(f"Failed to resolve URN/URL '{urn_str}': {e}")
            return self._entries.get(urn_str)

    def search_catalog(
        self,
        query: Optional[str] = None,
        resource_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Searches the catalog by text query, resource type, or tags."""
        results = []
        seen = set()

        for entry in self._entries.values():
            if entry["urn"] in seen:
                continue

            # Type filter
            if resource_type and entry["resource_type"].lower() != resource_type.lower():
                continue

            # Tag filter
            if tags and not any(t.lower() in [et.lower() for et in entry.get("tags", [])] for t in tags):
                continue

            # Query text search
            if query:
                q = query.lower()
                match = (
                    q in entry["name"].lower()
                    or q in entry["description"].lower()
                    or any(q in t.lower() for t in entry.get("tags", []))
                )
                if not match:
                    continue

            seen.add(entry["urn"])
            results.append(entry)

        return results

    def import_module(self, urn_str: str, target_project_id: str) -> Dict[str, Any]:
        """Imports a catalog entry as a module/dependency into a target project space."""
        entry = self.resolve_urn(urn_str)
        if not entry:
            return {"status": "error", "message": f"URN '{urn_str}' not found in catalog."}

        logger.info(f"Importing catalog module {urn_str} into project {target_project_id}")
        parsed = CoreasonURN.parse(entry["urn"])
        return {
            "status": "success",
            "imported_urn": entry["urn"],
            "oid_urn": parsed.to_oid_urn(),
            "coreason_url": parsed.to_coreason_url(),
            "name": entry["name"],
            "resource_type": entry["resource_type"],
            "target_project_id": target_project_id,
            "message": f"Successfully imported '{entry['name']}' as a modular component.",
        }


catalog_service = CatalogService()
