import os
import uuid
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

from deepagents.graph import create_deep_agent
from src.core.config import settings

logger = logging.getLogger(__name__)

@tool
def ask_clarifying_question(question: str) -> str:
    """Use this tool when you need to interrogate the human team to clarify architectural ambiguity. 
    It will pause your execution and prompt the humans for consensus."""
    return "User response will be injected here upon resumption."

class FactoryCeoAgent(DeepAgent):
    """
    Multi-User Collaborative Deep Agent for factory_ceo.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        # Load Multiple Choice Interrogation Skill
        skill_path = os.path.join(os.path.dirname(__file__), "..", "..", "core", "skills", "building", "multiple_choice_interrogation.md")
        skill_content = ""
        if os.path.exists(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                skill_content = f.read()

        base_prompt = self.agent_spec.get("system_prompt", "You are an expert orchestrator.")
        multi_user_prompt = """
You are collaborating with a team of humans. The `name` field on each human message identifies the speaker.
Resolve conflicts organically by mediating and asking the team for consensus before taking destructive actions.
If the architectural summary from the librarian is present and fully resolves the topology, proceed.
If you need more information from the team to resolve ambiguities, use the `ask_clarifying_question` tool.
"""
        full_system_prompt = f"{base_prompt}\n{multi_user_prompt}\n<SKILL: multiple_choice_interrogation>\n{skill_content}\n</SKILL>"
        self.system_prompt = full_system_prompt

    async def execute(self, context: dict, session_id: str = None) -> Any:
        is_goal_mode = context.get("is_goal_mode", False)
        
        prompt = self.system_prompt
        agent_tools = [ask_clarifying_question]
        agent_interrupt_on = {"ask_clarifying_question": True}
        
        if is_goal_mode:
            prompt += "\nGOAL MODE ACTIVE: You are running in fully autonomous mode. Do NOT ask for human clarification or consensus. Make the most reasonable architectural assumptions based on the context provided, be extra thorough, and continue delegating until the final deployment artifacts are fully generated."
            agent_tools = []
            agent_interrupt_on = {}

        from src.core.services.observability_service import ObservabilityService
        obs = ObservabilityService()

        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        from src.agents.librarian_pm.orchestrator import LibrarianPmAgent
        from src.agents.agent_pm.orchestrator import AgentPmAgent
        from src.agents.research_agent.orchestrator import ResearchAgent
        
        from langchain_core.messages import AIMessage
        # Subagents exposed to the CEO
        subagents = [
            {
                "name": "librarian_pm",
                "description": "Delegates codebase extraction and indexing. Must be called if a file path is provided.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=LibrarianPmAgent().execute(inputs, session_id=config["configurable"]["thread_id"]))]})
            },
            {
                "name": "agent_pm",
                "description": "Delegates saturated context to build the agent architecture.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=AgentPmAgent().execute(inputs, session_id=config["configurable"]["thread_id"], config=config))]})
            },
            {
                "name": "research_agent",
                "description": "Searches the internet for required factual context, news, or domain-specific information.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=ResearchAgent().execute(inputs, session_id=config["configurable"]["thread_id"], config=config))]})
            }
        ]

        async with AsyncPostgresSaver.from_conn_string(obs.pg_dsn) as checkpointer:
            await checkpointer.setup()
            
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=settings.LLM_MODEL_NAME,
                api_key=settings.LLM_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                base_url=settings.LLM_BASE_URL
            )
            
            # Construct the multi-user deep agent dynamically
            graph = create_deep_agent(
                model=llm,
                system_prompt=prompt,
                state_schema=DeepAgentState,
                tools=agent_tools,
                subagents=subagents,
                interrupt_on=agent_interrupt_on,
                checkpointer=checkpointer
            )
            
            config = {
                "configurable": {"thread_id": session_id or str(uuid.uuid7())}
            }

            state = await graph.aget_state(config)
            if state and getattr(state, "next", None):
                from langgraph.types import Command
                user_reply = context.get("raw_transcript", "")
                
                decisions = []
                # Try to inspect tasks for the interrupt payload to get the number of action requests
                if hasattr(state, "tasks") and state.tasks:
                    for task in state.tasks:
                        if task.interrupts:
                            for interrupt in task.interrupts:
                                val = interrupt.value if hasattr(interrupt, "value") else interrupt
                                if isinstance(val, dict) and "action_requests" in val:
                                    for req in val["action_requests"]:
                                        decisions.append({
                                            "type": "respond",
                                            "message": user_reply
                                        })
                
                # Fallback if we couldn't parse it
                if not decisions:
                    decisions = [{"type": "respond", "message": user_reply}]
                    
                resume_payload = {"decisions": decisions}
                return await graph.ainvoke(Command(resume=resume_payload), config=config)
            else:
                return await graph.ainvoke(context, config=config)
