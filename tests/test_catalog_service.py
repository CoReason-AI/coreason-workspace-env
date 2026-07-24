import pytest
from src.core.ontology import CoreasonURN
from src.core.services.catalog_service import catalog_service

def test_urn_parsing_pen_66197():
    # Test OID URN
    oid_urn = "urn:oid:1.3.6.1.4.1.66197:project:epistemic_v1"
    urn_obj = CoreasonURN.parse(oid_urn)
    assert urn_obj.pen == 66197
    assert urn_obj.resource_type == "project"
    assert urn_obj.resource_id == "epistemic_v1"
    assert urn_obj.to_coreason_url() == "https://urn.coreason.ai/1.3.6.1.4.1.66197/project/epistemic_v1"
    
    # Test Coreason URL format
    url_str = "https://urn.coreason.ai/1.3.6.1.4.1.66197/agent/yaml_compiler"
    url_obj = CoreasonURN.parse(url_str)
    assert url_obj.pen == 66197
    assert url_obj.resource_type == "agent"
    assert url_obj.to_oid_urn() == "urn:oid:1.3.6.1.4.1.66197:agent:yaml_compiler"

def test_catalog_service_search_and_resolve():
    # Test default seed search
    results = catalog_service.search_catalog(query="mcp")
    assert len(results) >= 1
    
    # Test resolve OID URN
    oid_urn = "urn:oid:1.3.6.1.4.1.66197:agent:yaml_compiler_agent"
    entry = catalog_service.resolve_urn(oid_urn)
    assert entry is not None
    assert entry["name"] == "YAML Compiler Agent"
    
    # Test resolve Coreason URL
    url_str = "https://urn.coreason.ai/1.3.6.1.4.1.66197/project/epistemic_analyst_v1"
    entry2 = catalog_service.resolve_urn(url_str)
    assert entry2 is not None
    assert entry2["name"] == "Epistemic Analyst Pipeline"

def test_catalog_service_registration():
    urn = "urn:oid:1.3.6.1.4.1.66197:skill:dowhy_causal_reasoning"
    entry = catalog_service.register_entry(
        urn=urn,
        name="DoWhy Causal Reasoning Skill",
        description="Formal causal graph estimation using Hill's criteria and DoWhy.",
        resource_type="skill",
        tags=["causal", "dowhy"],
        metadata={"author": "Coreason AI"}
    )
    assert entry.urn == urn
    
    # Test resolution by Coreason URL
    url_str = "https://urn.coreason.ai/1.3.6.1.4.1.66197/skill/dowhy_causal_reasoning"
    fetched = catalog_service.resolve_urn(url_str)
    assert fetched is not None
    assert fetched["name"] == "DoWhy Causal Reasoning Skill"

def test_catalog_service_import_module():
    res = catalog_service.import_module("urn:oid:1.3.6.1.4.1.66197:project:epistemic_analyst_v1", "target_proj_999")
    assert res["status"] == "success"
    assert res["target_project_id"] == "target_proj_999"
    assert "coreason_url" in res
