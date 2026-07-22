import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

from deepagents.graph import create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import PrivateAttr
import litellm

from src.core.services.agent_service import AgentService
from src.core.config import settings

logger = logging.getLogger(__name__)

class NativeLiteLLMModel(BaseChatModel):
    model: str
    temperature: float = 0.0
    api_key: str = ""
    api_base: str = ""

    def _format_messages(self, messages: list[BaseMessage]) -> list[dict]:
        litellm_messages = []
        for m in messages:
            if isinstance(m, HumanMessage) or m.type == "human":
                litellm_messages.append({"role": "user", "content": str(m.content)})
            elif isinstance(m, SystemMessage) or m.type == "system":
                litellm_messages.append({"role": "system", "content": str(m.content)})
            elif isinstance(m, AIMessage) or m.type == "ai":
                litellm_messages.append({"role": "assistant", "content": str(m.content)})
            else:
                litellm_messages.append({"role": "user", "content": str(m.content)})
        return litellm_messages

    def _generate(self, messages: list[BaseMessage], stop: Optional[list[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> ChatResult:
        litellm_messages = self._format_messages(messages)
        response = litellm.completion(
            model=self.model,
            messages=litellm_messages,
            temperature=self.temperature,
            api_key=self.api_key if self.api_key else None,
            api_base=self.api_base if self.api_base else None,
            **kwargs
        )
        content = response.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    async def _agenerate(self, messages: list[BaseMessage], stop: Optional[list[str]] = None, run_manager: Optional[Any] = None, **kwargs: Any) -> ChatResult:
        litellm_messages = self._format_messages(messages)
        response = await litellm.acompletion(
            model=self.model,
            messages=litellm_messages,
            temperature=self.temperature,
            api_key=self.api_key if self.api_key else None,
            api_base=self.api_base if self.api_base else None,
            **kwargs
        )
        content = response.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "native-litellm"

from typing import TypedDict, Annotated
import operator

class DynamicAgentState(TypedDict):
    payload: dict
    messages: Annotated[list, operator.add]

class DeepAgentService:
    """
    Wraps the deepagents Python SDK.
    Dify delegates to this service via MCP when it wants to execute a native LangGraph DeepAgent.
    """

    def __init__(self):
        self.agent_service = AgentService()

    async def run_native_deepagent(self, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hydrates the agent definition from agent.yaml and executes it using deepagents v0.6.0+ SDK.
        """
        agent_data = self.agent_service.get_agent(agent_name)
        if not agent_data:
            return {"error": f"Agent {agent_name} not found locally."}

        system_prompt_str = agent_data.get("system_prompt", "You are a helpful assistant.")
        
        # Load skill paths relative to the backend root
        skill_paths = []
        if "skill_registry" in agent_data:
            for skill in agent_data["skill_registry"]:
                p = skill.get("path", "")
                if p:
                    if not p.endswith(".md"):
                        p += ".md"
                    skill_paths.append(f"/{p}")

        try:
            model = NativeLiteLLMModel(
                model=settings.LLM_MODEL_NAME,
                api_key=settings.LLM_API_KEY,
                api_base=settings.LLM_BASE_URL,
                temperature=settings.LLM_TEMPERATURE
            )

            agent = create_deep_agent(
                model=model,
                tools=[],
                system_prompt=system_prompt_str,
                state_schema=DynamicAgentState,
                skills=skill_paths
            )

            # Invoke the agent asynchronously
            input_state = {"payload": payload, "messages": []}
            result = await agent.ainvoke(input_state)

            final_message = ""
            if "messages" in result and len(result["messages"]) > 0:
                final_message = result["messages"][-1].content

            return {
                "status": "success",
                "agent_name": agent_name,
                "result": final_message,
                "raw_state": {
                    k: v for k, v in result.items() if k != "messages"
                }
            }
        except Exception as e:
            logger.error(f"DeepAgent execution failed: {e}")
            return {"error": str(e)}

deepagent_service = DeepAgentService()
