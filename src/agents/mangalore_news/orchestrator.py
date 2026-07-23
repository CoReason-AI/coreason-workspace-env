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
    """Searches the internet for local Mangalore news and recent updates."""
    logger.info(f"*** TOOL CALL: search_internet('{query}') ***")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if tavily_key:
        try:
            logger.info("Using Tavily for search...")
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            response = client.search(query=f"Mangalore news {query}", search_depth="basic")
            results = []
            for r in response.get("results", []):
                results.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}\n")
            
            final_res = "\n".join(results)
            if final_res.strip():
                return final_res
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            
    # Fallback search API
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Mangalore+{query}&utf8=&format=json"
        response = httpx.get(wiki_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10.0)
        data = response.json()
        results = []
        for r in data.get("query", {}).get("search", [])[:3]:
            import re
            snippet = re.sub(r'<[^>]+>', '', r.get("snippet", ""))
            results.append(f"Title: {r.get('title')}\nSnippet: {snippet}\n")
        
        if not results:
            return "No local news results found for the query."
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Fallback search failed: {e}")
        return f"Search failed. Error: {e}"

class MangaloreNewsAgent(DeepAgent):
    """
    Autonomous agent discussing local news in Mangalore, India.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        self.system_prompt = self.agent_spec.get("system_prompt", "You are an autonomous Mangalore News Agent.")

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes news discussion using a ReAct deep agent.
        """
        logger.info(f"[{session_id}] MangaloreNewsAgent executing query.")
        
        internal_thread_id = f"{session_id or str(uuid.uuid7())}-mangalore"
        internal_config = {
            "configurable": {"thread_id": internal_thread_id},
            "recursion_limit": 5
        }
        
        initial_state = {"messages": context} if isinstance(context, list) else {"messages": [("user", str(context))]}
        
        graph = self.build_standard_deep_agent(
            system_prompt=self.system_prompt,
            state_schema=DeepAgentState,
            subagents=[],
            tools=[search_internet]
        )
        
        try:
            result = graph.invoke(initial_state, config=internal_config)
        except Exception as e:
            logger.warning(f"MangaloreNewsAgent graph stopped early: {e}")
            result = {}
            
        messages = result.get("messages", [])
        if not messages:
            return "FAILURE: No output produced."
        
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                if len(msg.content.strip()) > 10:
                    return msg.content
            if msg.__class__.__name__ == "ToolMessage":
                return f"Mangalore Local News Updates:\n{msg.content}"
        
        return "FAILURE: Empty content received from model."
