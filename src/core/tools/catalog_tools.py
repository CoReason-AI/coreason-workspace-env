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


@tool
def forge_tool_tool(
    tool_id: str,
    name: str,
    description: str,
    code: str,
    unit_test_code: str,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Forge a new tool: runs Maker-Checker sandbox validation, executes unit tests,
    and registers the verified tool into the global catalog under IANA PEN 66197 URN.
    """
    from src.core.services.tool_forging_service import tool_forging_service
    return tool_forging_service.forge_tool(
        tool_id=tool_id,
        name=name,
        description=description,
        code=code,
        unit_test_code=unit_test_code,
        tags=tags
    )


@tool
def forge_skill_tool(
    skill_id: str,
    name: str,
    category: str,
    description: str,
    content: str,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Forge a new agent skill markdown document: writes skill file to registry
    and registers it into the global catalog under IANA PEN 66197 URN.
    """
    from src.core.services.skill_service import skill_service
    return skill_service.forge_skill(
        skill_id=skill_id,
        name=name,
        category=category,
        description=description,
        content=content,
        tags=tags
    )


@tool
def clone_skill_tool(urn_or_id: str, target_category: Optional[str] = None) -> Dict[str, Any]:
    """
    Clone an existing skill from the global catalog (PEN 66197 URN) into the local skill registry.
    """
    from src.core.services.skill_service import skill_service
    return skill_service.clone_skill(urn_or_id, target_category)
