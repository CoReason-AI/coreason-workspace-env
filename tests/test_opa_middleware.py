import pytest
import httpx
from uuid import uuid4
from src.core.security.opa_middleware import OPAAuthzCallbackHandler, OPAPermissionError
from src.core.config import settings
from unittest.mock import patch, AsyncMock

@pytest.fixture(autouse=True)
def enable_opa():
    """Ensure OPA IAM is enabled for tests."""
    original = settings.ENABLE_OPA_IAM
    settings.ENABLE_OPA_IAM = True
    yield
    settings.ENABLE_OPA_IAM = original

@pytest.mark.asyncio
async def test_on_tool_start_allowed():
    # Mock httpx response for ALLOW
    mock_response = httpx.Response(200, json={"result": True}, request=httpx.Request("POST", "http://test"))
    
    handler = OPAAuthzCallbackHandler(agent_id="factory_ceo")
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        # Should execute silently without raising an exception
        await handler.on_tool_start(
            serialized={"name": "test_tool"},
            input_str="{}",
            run_id=uuid4(),
            inputs={"arg": "val"}
        )

@pytest.mark.asyncio
async def test_on_tool_start_denied():
    # Mock httpx response for DENY
    mock_response = httpx.Response(200, json={"result": False}, request=httpx.Request("POST", "http://test"))
    
    handler = OPAAuthzCallbackHandler(agent_id="unauthorized_agent")
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        with pytest.raises(OPAPermissionError, match="Access denied by OPA policy"):
            await handler.on_tool_start(
                serialized={"name": "secret_tool"},
                input_str="{}",
                run_id=uuid4(),
                inputs={"arg": "val"}
            )

@pytest.mark.asyncio
async def test_on_tool_start_disabled():
    settings.ENABLE_OPA_IAM = False
    handler = OPAAuthzCallbackHandler(agent_id="factory_ceo")
    # Even without a mock, it should return silently
    await handler.on_tool_start(
        serialized={"name": "any_tool"},
        input_str="{}",
        run_id=uuid4()
    )
