import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.services.observability_service import ObservabilityService

@pytest.fixture
def obs_service():
    return ObservabilityService()

@pytest.mark.asyncio
async def test_fetch_postgres_state(obs_service, mocker):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "thread_id": "test-session",
        "state": '{"status": "ok"}'
    }
    
    mock_connect = mocker.patch("src.core.services.observability_service.asyncpg.connect", return_value=mock_conn)
    
    result = await obs_service.fetch_postgres_state("test-session")
    
    mock_connect.assert_called_once()
    mock_conn.fetchrow.assert_called_once()
    assert result["thread_id"] == "test-session"
    assert result["state"] == {"status": "ok"}

@pytest.mark.asyncio
async def test_fetch_langfuse_traces(obs_service, mocker):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"trace_id": "123"}]}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    
    mocker.patch("src.core.services.observability_service.httpx.AsyncClient", return_value=mock_client)
    
    obs_service.langfuse_public = "test_pub"
    obs_service.langfuse_secret = "test_sec"
    
    result = await obs_service.fetch_langfuse_traces("test-session")
    
    assert "data" in result
    assert result["data"][0]["trace_id"] == "123"

@pytest.mark.asyncio
async def test_write_dev_vault_secret(obs_service, mocker):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    
    mocker.patch("src.core.services.observability_service.httpx.AsyncClient", return_value=mock_client)
    
    result = await obs_service.write_dev_vault_secret("secret/agent-keys", {"key": "val"})
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_resume_agent(obs_service, mocker):
    mock_enqueue = mocker.patch("src.core.queue.DistributedTaskQueue.enqueue_workflow")
    
    result = await obs_service.resume_agent("test-session", "factory_ceo", {"foo": "bar"})
    
    mock_enqueue.assert_called_once_with(
        session_id="test-session",
        agent_name="factory_ceo",
        payload={"foo": "bar"}
    )
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_fetch_docker_logs(obs_service, mocker):
    mock_run = mocker.patch("src.core.services.observability_service.subprocess.run")
    mock_run.return_value = MagicMock(stdout="Log line 1\nLog line 2", stderr="")
    
    result = await obs_service.fetch_docker_logs(10)
    
    assert "Log line 1" in result
    mock_run.assert_called_once()
