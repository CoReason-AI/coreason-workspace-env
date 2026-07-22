import pytest
from src.core.services.sandbox_service import sandbox_service

def test_sandbox_lifecycle():
    project_id = "test_project_sbx_123"
    
    # 1. Provision Sandbox
    rec = sandbox_service.provision_sandbox(
        project_id=project_id,
        user_id="usr_test",
        tenant_id="tnt_test",
        environment="test",
        secrets={"CUSTOM_KEY": "custom_val_123"},
        connections={"custom_db": "postgresql://user:pass@localhost:5432/db"},
        mcp_servers=["coreason-filesystem"]
    )
    
    assert rec.sandbox_id is not None
    assert rec.project_id == project_id
    assert rec.status == "running"
    assert rec.provisioned_secrets["CUSTOM_KEY"] == "custom_val_123"
    assert "custom_db" in rec.connections
    
    # 2. Get Sandbox
    fetched = sandbox_service.get_sandbox(rec.sandbox_id)
    assert fetched is not None
    assert fetched["sandbox_id"] == rec.sandbox_id
    
    # 3. List Sandboxes
    all_sbx = sandbox_service.list_sandboxes(project_id=project_id)
    assert len(all_sbx) >= 1
    
    # 4. Execute in Sandbox
    exec_res = sandbox_service.execute_in_sandbox(
        sandbox_id=rec.sandbox_id,
        payload={"query": "test query inside sandbox"}
    )
    assert exec_res["status"] == "success"
    assert exec_res["sandbox_id"] == rec.sandbox_id
    
    # 5. Terminate Sandbox
    term_res = sandbox_service.terminate_sandbox(rec.sandbox_id)
    assert term_res["status"] == "success"
    
    # Verify terminated state
    after_term = sandbox_service.get_sandbox(rec.sandbox_id)
    assert after_term["status"] == "terminated"
