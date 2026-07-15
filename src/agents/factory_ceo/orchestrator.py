from typing import Any, Dict, TypedDict
import uuid
import os
import yaml
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from src.core.ontology import (
    EpistemicQuarantineSnapshot,
    EpistemicProxyState,
    OrchestratorCeoState
)
from src.core.services.worm_storage import persist_quarantine_snapshot

import logging
logger = logging.getLogger(__name__)

async def epistemic_interceptor_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph Node that physically intercepts large raw human transcripts
    BEFORE they enter the factory_ceo's context window.
    """
    raw_payload = state.get("raw_transcript")
    
    if raw_payload:
        snapshot = EpistemicQuarantineSnapshot(
            snapshot_id=str(uuid.uuid7()),
            raw_payload=raw_payload
        )
        
        # Persist to WORM Postgres table via core service (Body infrastructure)
        await persist_quarantine_snapshot(snapshot)
        
        proxy = EpistemicProxyState(
            proxy_cid=snapshot.snapshot_id,
            structural_type="HumanTranscript"
        )
        
        return {
            "raw_transcript": None,
            "epistemic_proxy": proxy
        }
        
    return {}

def evaluate_context(state: OrchestratorCeoState) -> dict:
    """
    Evaluates if the context is saturated enough to delegate.
    """
    from src.core.config import settings
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        base_url=settings.LLM_BASE_URL
    )
    
    context = "\n".join([m.content for m in state.get("messages", []) if isinstance(m, HumanMessage)])
    
    prompt = f"Evaluate this intent: '{context}'. Does it contain enough info to build an agent? Answer YES or NO."
    response = llm.invoke([SystemMessage(content=prompt)])
    
    is_saturated = "YES" in response.content.upper()
    return {"is_saturated": is_saturated}

def delegate_to_pm(state: OrchestratorCeoState) -> dict:
    """
    Delegates saturated context to the agent_pm.
    """
    logger.info("Context saturated. Delegating to agent_pm.")
    from src.agents.agent_pm.orchestrator import AgentPmAgent
    # Passing control to sub-agent
    pm = AgentPmAgent()
    if hasattr(pm, 'execute'):
        result = pm.execute(state)
        return {"messages": [SystemMessage(content=f"Delegation result: {result}")]}
    return {"messages": [SystemMessage(content="agent_pm executed successfully.")]}

def interrogate_user(state: OrchestratorCeoState) -> dict:
    """
    Asks user for more context.
    """
    return {"messages": [SystemMessage(content="Please provide more detailed requirements for your agent.")]}

def route_evaluation(state: OrchestratorCeoState) -> str:
    if state.get("is_saturated"):
        return "delegate"
    return "interrogate"

class FactoryCeoAgent(DeepAgent):
    """
    State Machine Orchestrator for factory_ceo.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        self.graph_builder = StateGraph(OrchestratorCeoState)
        self.graph_builder.add_node("interceptor", epistemic_interceptor_node)
        self.graph_builder.add_node("evaluator", evaluate_context)
        self.graph_builder.add_node("delegate", delegate_to_pm)
        self.graph_builder.add_node("interrogate", interrogate_user)
        
        self.graph_builder.set_entry_point("interceptor")
        self.graph_builder.add_edge("interceptor", "evaluator")
        self.graph_builder.add_conditional_edges(
            "evaluator",
            route_evaluation,
            {"delegate": "delegate", "interrogate": "interrogate"}
        )
        self.graph_builder.add_edge("delegate", END)
        self.graph_builder.add_edge("interrogate", END)
        
        self.graph = self.graph_builder.compile()

    async def execute(self, context: dict, session_id: str = None) -> Any:
        return await self.graph.ainvoke(context, config={"configurable": {"thread_id": session_id or str(uuid.uuid7())}})
