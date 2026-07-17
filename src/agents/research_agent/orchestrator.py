import os
import uuid
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState
from langchain_core.tools import tool
import httpx

logger = logging.getLogger(__name__)

@tool
def search_internet(query: str) -> str:
    """Searches the internet for the given query and returns a summary of the results."""
    logger.info(f"*** TOOL CALL: search_internet('{query}') ***")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if tavily_key:
        try:
            logger.info("Using Tavily for search...")
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            response = client.search(query=query, search_depth="basic")
            results = []
            for r in response.get("results", []):
                results.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}\n")
            
            final_res = "\n".join(results)
            if not final_res.strip():
                final_res = "No results found for the query."
            logger.info(f"Tavily returned {len(results)} results.")
            return final_res
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            
    # Fallback to Wikipedia search API
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
        response = httpx.get(wiki_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10.0)
        data = response.json()
        results = []
        for r in data.get("query", {}).get("search", [])[:3]:
            import re
            snippet = re.sub(r'<[^>]+>', '', r.get("snippet", ""))
            results.append(f"Title: {r.get('title')}\nSnippet: {snippet}\n")
        
        if not results:
            return "No results found for the query."
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Fallback Wikipedia search failed: {e}")
        return f"Search failed. Error: {e}"

class ResearchAgent(DeepAgent):
    """
    Deterministic subagent for searching the internet.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        self.system_prompt = self.agent_spec.get("system_prompt", "You are an autonomous Research Agent.")

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes pipeline using a ReAct deep agent.
        """
        logger.info(f"[{session_id}] ResearchAgent initiating search.")
        
        internal_thread_id = f"{session_id or str(uuid.uuid7())}-research"
        internal_config = {
            "configurable": {"thread_id": internal_thread_id},
            "recursion_limit": 5
        }
        
        initial_state = {"messages": context} if isinstance(context, list) else {"messages": [("user", str(context))]}
        
        from langgraph.checkpoint.postgres import PostgresSaver
        import psycopg
        from src.core.services.observability_service import ObservabilityService
        obs = ObservabilityService()
        
        with psycopg.connect(obs.pg_dsn) as conn:
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            
            graph = self.build_standard_deep_agent(
                system_prompt=self.system_prompt,
                state_schema=DeepAgentState,
                subagents=[],
                tools=[search_internet],
                checkpointer=checkpointer
            )
            try:
                result = graph.invoke(initial_state, config=internal_config)
            except Exception as e:
                logger.warning(f"ResearchAgent graph stopped early (e.g. recursion limit): {e}")
                result = graph.get_state(internal_config).values
            
        messages = result.get("messages", [])
        logger.info(f"ResearchAgent final messages: {[type(m).__name__ + ': ' + str(m.content)[:100] for m in messages]}")
        if not messages:
            return "FAILURE: No output produced."
        
        # Try to find the last substantive text message or ToolMessage
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                if len(msg.content.strip()) > 10:
                    return msg.content
            if msg.__class__.__name__ == "ToolMessage":
                return f"Raw Search Results:\n{msg.content}"
        
        return "FAILURE: Empty content received from model."
