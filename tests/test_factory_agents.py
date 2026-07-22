import pytest
import os
from src.agents.agent_validator.orchestrator import AgentValidatorAgent
from src.agents.agent_pm.orchestrator import AgentPmAgent
from src.agents.librarian_pm.orchestrator import LibrarianPmAgent
from src.agents.research_agent.orchestrator import ResearchAgent
from src.core.services.license_service import CloudKMSLicenseService

def test_agent_validator():
    validator = AgentValidatorAgent()
    
    # Test PASS case
    pass_manifest = {
        "name": "valid_agent",
        "system_prompt": "You are a helpful agent.",
        "skills": []
    }
    assert validator.execute(pass_manifest) == "PASS"
    
    # Test FAIL case
    fail_manifest = {
        "name": "",
        "system_prompt": ""
    }
    res = validator.execute(fail_manifest)
    assert res.startswith("FAIL")

def test_cloud_kms_license_service():
    svc = CloudKMSLicenseService()
    assert svc.kms_provider == "aws"

def test_librarian_pm_instantiation():
    agent = LibrarianPmAgent()
    assert agent.system_prompt is not None

def test_research_agent_instantiation():
    agent = ResearchAgent()
    assert agent.system_prompt is not None

def test_agent_pm_execution():
    pm = AgentPmAgent()
    res = pm.execute("Create a minimal test agent named test_bot", session_id="test_session_pm_1")
    assert res is not None
    assert isinstance(res, str)
