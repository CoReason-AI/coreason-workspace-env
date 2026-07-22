"""
LangGraph Tools for Catalog & URN Authority (PEN 66197).
Allows building agents (factory_ceo, agent_pm, librarian_pm) to search, resolve, and import catalog modules.
"""
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from src.core.services import catalog_service


@tool
def search_catalog_tool(query: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search the Coreason Project & Module Catalog (PEN 66197 Authority) for similar past projects,
    agents, skills, or components to reuse or review.
    """
    return catalog_service.search_catalog(query=query, resource_type=resource_type)


@tool
def resolve_urn_tool(urn: str) -> Dict[str, Any]:
    """
    Resolve an OID URN (urn:oid:1.3.6.1.4.1.66197:...) or Native URN (urn:coreason:...)
    to retrieve its complete metadata, schema, and source code.
    """
    res = catalog_service.resolve_urn(urn)
    return res or {"error": f"URN '{urn}' not found."}


@tool
def import_catalog_module_tool(urn: str, target_project_id: str) -> Dict[str, Any]:
    """
    Import a cataloged project, agent, or component module into a target project space.
    """
    return catalog_service.import_module(urn, target_project_id)
