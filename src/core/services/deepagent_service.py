import logging
from typing import Dict, Any, Optional, TypedDict, Annotated
import operator

from deepagents.graph import create_deep_agent
from langchain_openai import ChatOpenAI

from src.core.services.agent_service import AgentService
from src.core.config import settings

logger = logging.getLogger(__name__)


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
            model = ChatOpenAI(
                model=settings.LLM_MODEL_NAME,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                temperature=settings.LLM_TEMPERATURE,
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
