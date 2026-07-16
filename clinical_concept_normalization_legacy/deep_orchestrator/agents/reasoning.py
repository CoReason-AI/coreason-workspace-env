from typing import Any, Sequence
from langchain_core.tools import BaseTool
from deepagents import create_deep_agent
from ..state import GlobalSwarmState

def build_reasoning_node(name: str, model: str, system_prompt: Any, tools: Sequence[BaseTool] | None = None, backend: Any = None, **kwargs):
    """Builds a Deep Agent wrapped in a LangGraph node.
    
    This factory automatically provisions the Deep Agents Harness and Sandbox
    for the generated LLM reasoning agent.
    """
    
    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools or [],
        state_schema=GlobalSwarmState,
        backend=backend,
        **kwargs
    )
    
    def node_function(state: GlobalSwarmState) -> dict:
        result = agent.invoke(state)
        # Deep Agents output updated messages
        messages = result.get("messages", [])
        return {
            "messages": messages,
            "sender": name
        }
    
    return node_function
