from typing import Any, Callable, Sequence
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import BaseTool

from ..state import GlobalSwarmState
from ..agents.reasoning import build_reasoning_node
from ..agents.script import build_script_node
from .routing import supervisor_router

class SwarmOrchestrator:
    """Wrapper around LangGraph's StateGraph to simplify multi-agent orchestration."""
    
    def __init__(self, backend: Any = None):
        self.builder = StateGraph(GlobalSwarmState)
        self.backend = backend
        self.agents = []
        self.entry_point = None
        
    def add_reasoning_agent(self, name: str, model: str, system_prompt: Any, tools: Sequence[BaseTool] | None = None, **kwargs):
        """Adds an LLM-backed Deep Agent to the swarm."""
        node = build_reasoning_node(name, model, system_prompt, tools, self.backend, **kwargs)
        self.builder.add_node(name, node)
        self.agents.append(name)
        
    def add_script_agent(self, name: str, func: Callable):
        """Adds a pure Python deterministic function to the swarm as a peer agent."""
        node = build_script_node(name, func, self.backend)
        self.builder.add_node(name, node)
        self.agents.append(name)
        
    def add_peer_connection(self, from_agent: str, to_agent: str):
        """Creates a direct transition edge between two agents."""
        self.builder.add_edge(from_agent, to_agent)
        
    def set_entry_point(self, name: str):
        """Sets the first agent that receives control when the graph is invoked."""
        self.entry_point = name
        self.builder.add_edge(START, name)
        
    def set_supervisor_routing(self, from_agent: str, target_agents: list[str]):
        """Creates a dynamic conditional routing point (e.g. for a Supervisor agent).
        
        The 'from_agent' must update the 'next_agent' state key to dictate flow.
        """
        route_map = {agent: agent for agent in target_agents}
        route_map["__end__"] = END
        self.builder.add_conditional_edges(from_agent, supervisor_router, route_map)

    def compile(self, checkpointer=None):
        """Compiles the orchestrator into an executable LangGraph application."""
        if not self.entry_point and self.agents:
            self.set_entry_point(self.agents[0])
        return self.builder.compile(checkpointer=checkpointer)
