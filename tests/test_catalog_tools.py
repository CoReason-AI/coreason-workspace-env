import pytest
from src.core.tools.catalog_tools import search_catalog_tool, resolve_urn_tool, import_catalog_module_tool

def test_catalog_langgraph_tools():
    # 1. Search tool
    res = search_catalog_tool.invoke({"query": "epistemic"})
    assert isinstance(res, list)
    assert len(res) >= 1
    
    # 2. Resolve URN tool
    urn_res = resolve_urn_tool.invoke({"urn": "urn:oid:1.3.6.1.4.1.66197:project:epistemic_analyst_v1"})
    assert "name" in urn_res
    assert urn_res["name"] == "Epistemic Analyst Pipeline"
    
    # 3. Import module tool
    imp_res = import_catalog_module_tool.invoke({
        "urn": "urn:coreason:agent:yaml_compiler_agent",
        "target_project_id": "proj_tool_test_123"
    })
    assert imp_res["status"] == "success"
    assert imp_res["target_project_id"] == "proj_tool_test_123"
