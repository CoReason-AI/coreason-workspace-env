import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from src.core.config import settings

import yaml
import os

logger = logging.getLogger(__name__)

class PlatformOrchestrator:
    """
    Decoupled Platform Orchestrator (The Harness Body).
    This class handles the generic routing and LangGraph execution context for any Project Plugin.
    It manages the CISO-grade Checkpointer connection and the native MCP tool injection.
    """
    def __init__(self, project_manifest: Dict[str, Any], agent_name: str = None):
        """
        Initializes the generic orchestrator using the dynamically loaded project.yaml manifest.
        Loads the active Agent Definition (The Brain) dynamically via AGENT_DEF_PATH.
        """
        self.project_manifest = project_manifest
        
        # Determine active Agent Definition path
        agent_def_path = os.environ.get("AGENT_DEF_PATH")
        if not agent_def_path:
            # Default to the built-in agents directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if agent_name:
                agent_def_path = os.path.join(base_dir, "agents", agent_name)
            else:
                agent_def_path = os.path.join(base_dir, "agents")
            
        # Load core pyagentspec yaml from the active Brain
        yaml_path = os.path.join(agent_def_path, "agent.yaml")
        
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Missing Brain definition at {yaml_path}")
            
        with open(yaml_path, "r") as f:
            agent_spec = yaml.safe_load(f)
            
        self.agent_name = agent_spec.get("name", "PlatformOrchestrator")
        self.system_prompt = agent_spec.get("system_prompt", "You are a helpful assistant.")
        
        # Connect to Postgres Checkpointer using strict CISO SSOT config
        self.project_id = self.project_manifest.get("id", "default")
        self.schema_name = f"project_{self.project_id.replace('-', '_')}"
        
        self.db_uri = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        self.pool = AsyncConnectionPool(
            conninfo=self.db_uri, 
            max_size=20, 
            timeout=2.0, 
            kwargs={
                "autocommit": True,
                "options": f"-c search_path={self.schema_name}"
            }
        )
        
        self.llm = ChatOpenAI(
            model=project_manifest.get("model", settings.LLM_MODEL_NAME),
            base_url=project_manifest.get("base_url", settings.LLM_BASE_URL),
            api_key=project_manifest.get("api_key", settings.LLM_API_KEY), # Handled by Vault in reality
            temperature=project_manifest.get("temperature", settings.LLM_TEMPERATURE),
            max_retries=0
        )
        
        logger.info(f"PlatformOrchestrator initialized with Brain: {self.agent_name} at {agent_def_path}")

    def get_dynamic_tools(self) -> List[Any]:
        """
        Loads the MCP tools and Project Plugin specific tools dynamically.
        """
        return []

    async def execute_graph(self, session_id: str, user_input: str) -> str:
        """
        Compiles and executes the LangGraph using the Postgres checkpointer for state retention.
        """
        try:
            import asyncpg
            sys_conn = await asyncpg.connect(self.db_uri)
            await sys_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")
            await sys_conn.close()

            async with self.pool:
                from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
                custom_serde = JsonPlusSerializer(
                    allowed_msgpack_modules=[
                        ("src.core.ontology", "EpistemicProxyState"),
                        ("src.core.ontology", "EpistemicQuarantineSnapshot"),
                        ("src.core.ontology", "OrchestratorCeoState")
                    ]
                )
                checkpointer = AsyncPostgresSaver(self.pool, serde=custom_serde)
                await checkpointer.setup()
                
                from langgraph.store.postgres import AsyncPostgresStore
                from langchain_openai import OpenAIEmbeddings
                
                store = AsyncPostgresStore(
                    self.pool,
                    index={
                        "dims": 1536,
                        "embed": OpenAIEmbeddings(
                            model=settings.EMBEDDING_MODEL_NAME,
                            base_url=settings.LLM_BASE_URL,
                            api_key=settings.LLM_API_KEY,
                            max_retries=0
                        ),
                        "fields": ["content"]
                    }
                )
                await store.setup()
                
                from deepagents import create_deep_agent
                
                # In a true distributed system, this node execution is published to Redis/Celery.
                graph = create_deep_agent(
                    model=self.llm,
                    tools=self.get_dynamic_tools(),
                    checkpointer=checkpointer,
                    store=store
                )
                
                config = {"configurable": {"thread_id": session_id}}
                logger.info(f"Executing graph for session {session_id}")
                
                result = await graph.ainvoke(
                    {"messages": [("user", user_input)]},
                    config=config
                )
                
                return result['messages'][-1].content
        except Exception as e:
            logger.error(f"Failed to execute graph: {e}")
            raise
