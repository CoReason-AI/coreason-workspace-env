from typing import Annotated, Any
from typing_extensions import TypedDict
from deepagents.graph import DeepAgentState

class GlobalSwarmState(DeepAgentState):
    """Shared state for the multi-agent swarm."""
    next_agent: str
    sender: str
