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
Initial Interaction Protocol:
1. Search the built-in Project Catalog (`catalog_service`) powered by IANA PEN 66197 (`urn:oid:1.3.6.1.4.1.66197:...`).
2. Present relevant past project exemplars to the human team so they can review, learn, and import modular building blocks.
If the architectural summary from the librarian is present and fully resolves the topology, proceed.
If you need more information from the team to resolve ambiguities, use the `ask_clarifying_question` tool.
"""
        output_architectural_opinions = """
FRACTAL ARCHITECTURAL OPINIONS FOR GENERATED AGENTIC APPLICATIONS:
Every agentic application synthesized by this factory MUST mirror the platform's self-similar opinionated architecture:
1. DeepAgent Manifests & StateGraphs: PyAgentSpec-compliant YAML manifests with strict TypedDict state schemas.
2. 5-Surface Parity: Embedded REST API, CLI, MCP Server, WebSockets/SSE, and Python SDK transport adapters over a shared core service layer.
3. Headless & Dify Enterprise Shell Integration: Exposed natively as an MCP server to allow Dify or external AI orchestrators to control the app natively.
4. IANA PEN 66197 Identifiers: Assigned a canonical OID URN (`urn:oid:1.3.6.1.4.1.66197:<type>:<id>`) and Coreason URL (`https://urn.coreason.ai/1.3.6.1.4.1.66197/...`).
5. Open-Source Observability: Embedded OpenTelemetry + Langfuse tracing without proprietary SaaS lock-in.
6. Sandboxed Testing: Self-contained execution sandboxes for multi-tenant project spaces.
"""
        full_system_prompt = f"{base_prompt}\n{multi_user_prompt}\n{output_architectural_opinions}\n<SKILL: multiple_choice_interrogation>\n{skill_content}\n</SKILL>"
        self.system_prompt = full_system_prompt

    async def execute(self, context: dict, session_id: str = None) -> Any:
        is_goal_mode = context.get("is_goal_mode", False)
        prompt = self.system_prompt
        from src.core.tools.catalog_tools import search_catalog_tool, resolve_urn_tool, import_catalog_module_tool
        agent_tools = [ask_clarifying_question, search_catalog_tool, resolve_urn_tool, import_catalog_module_tool]
        agent_interrupt_on = {"ask_clarifying_question": True}
        
        if is_goal_mode:
            prompt += "\nGOAL MODE ACTIVE: You are running in fully autonomous mode. Do NOT ask for human clarification or consensus. Make the most reasonable architectural assumptions based on the context provided, be extra thorough, and delegate the final artifact compilation to `agent_pm`. Once `agent_pm` completes, you MUST repeat its output (the YAML blocks) exactly in your final response without any conversational summaries or extra explanation."
            agent_tools = [search_catalog_tool, resolve_urn_tool, import_catalog_module_tool]
            agent_interrupt_on = {}

        from src.core.config import settings
        import os
        pg_dsn = getattr(settings, "DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/db"))

        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        from src.agents.librarian_pm.orchestrator import LibrarianPmAgent
        from src.agents.agent_pm.orchestrator import AgentPmAgent
        from src.agents.research_agent.orchestrator import ResearchAgent
        
        from src.agents.agent_tester.orchestrator import AgentTesterAgent
        
        from langchain_core.messages import AIMessage
        from pydantic import BaseModel, Field
        class LibrarianPmInput(BaseModel):
            query: str = Field(description="The request or file paths to index.")
        class AgentPmInput(BaseModel):
            context: str = Field(description="The saturated context, architectural plan, and requirements to pass to the agent_pm for building.")
        class ResearchInput(BaseModel):
            query: str = Field(description="The search query.")
        class AgentTesterInput(BaseModel):
            context: str = Field(description="The finalized project context to generate E2E tests and acceptance criteria for.")

        # Subagents exposed to the CEO
        subagents = [
            {
                "name": "librarian_pm",
                "description": "Delegates codebase extraction and indexing. Must be called if a file path is provided.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=LibrarianPmAgent().execute(inputs, session_id=config["configurable"]["thread_id"]))]}).with_types(input_type=LibrarianPmInput)
            },
            {
                "name": "agent_pm",
                "description": "Delegates saturated context to build the agent architecture.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=AgentPmAgent().execute(inputs, session_id=config["configurable"]["thread_id"], config=config))]}).with_types(input_type=AgentPmInput)
            },
            {
                "name": "research_agent",
                "description": "Searches the internet for required factual context, news, or domain-specific information.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=ResearchAgent().execute(inputs, session_id=config["configurable"]["thread_id"], config=config))]}).with_types(input_type=ResearchInput)
            },
            {
                "name": "agent_tester",
                "description": "Delegates finalized project context to generate automated tests and acceptance criteria.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=AgentTesterAgent().execute(inputs, session_id=config["configurable"]["thread_id"], config=config))]}).with_types(input_type=AgentTesterInput)
            }
        ]

        async with AsyncPostgresSaver.from_conn_string(pg_dsn) as checkpointer:
            await checkpointer.setup()
            
            llm = self.get_chat_model()
            
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
            
            try:
                try:
                    from langfuse.langchain import CallbackHandler
                except ImportError:
                    from langfuse.callback import CallbackHandler
                langfuse_handler = CallbackHandler()
                config["callbacks"] = [langfuse_handler]
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse (skipping): {e}")

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
