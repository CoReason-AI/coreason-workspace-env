import logging
import httpx
from typing import Dict, Any, Optional
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.exceptions import OutputParserException
# Note: In a LangGraph setup, raising an exception during on_tool_start
# typically halts the tool execution. LangGraph can handle this gracefully 
# if handle_tool_errors is configured.
from langchain_core.tools import ToolException

from src.core.config import settings

logger = logging.getLogger(__name__)

class OPAPermissionError(ToolException):
    """Raised when an OPA policy explicitly denies access."""
    pass

class OPAAuthzCallbackHandler(AsyncCallbackHandler):
    """
    Native LangChain Callback Handler to enforce Open Policy Agent (OPA) IAM rules.
    Intercepts the `on_tool_start` event to ensure the agent has permissions 
    to execute the requested tool before it runs.
    """
    def __init__(self, agent_id: str, user_identity: Dict[str, Any] = None):
        super().__init__()
        self.agent_id = agent_id
        self.user_identity = user_identity or {"roles": ["default"]}
        
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Run when the tool starts running.
        """
        tool_name = serialized.get("name", "unknown_tool")
        
        if not settings.ENABLE_OPA_IAM:
            logger.debug(f"OPA IAM is disabled. Bypassing check for {self.agent_id}->{tool_name}")
            return
            
        # Build the OPA input payload
        input_data = {
            "input": {
                "agent": self.agent_id,
                "tool": tool_name,
                "payload": inputs or {"input_str": input_str},
                "user": self.user_identity
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.OPA_URL, 
                    json=input_data,
                    timeout=2.0
                )
                response.raise_for_status()
                
                result = response.json()
                is_allowed = result.get("result", False)
                
                if not is_allowed:
                    logger.warning(f"OPA Denied Access: {self.agent_id} attempted to use {tool_name}")
                    raise OPAPermissionError(f"Access denied by OPA policy for tool '{tool_name}'")
                    
                logger.info(f"OPA Granted Access: {self.agent_id} using {tool_name}")
                
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to OPA server at {settings.OPA_URL}: {e}")
            # In a strict zero-trust model, fail closed if OPA is unreachable
            raise OPAPermissionError("Authorization server unreachable. Access denied (fail-closed).")
