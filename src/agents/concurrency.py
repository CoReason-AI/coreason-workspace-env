import logging
from typing import Annotated, Any, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langgraph.prebuilt.tool_executor import ToolInvocation
from langgraph.errors import GraphInterrupt

logger = logging.getLogger(__name__)

# LangGraph State Channel Reducers for parallel map-reduce DAG state merging
def state_reducer(left: list[BaseMessage], right: list[BaseMessage]) -> list[BaseMessage]:
    """
    State reducer for parallel agent executions (e.g. Phase 2 deep research fanouts).
    Safely merges the message lists from concurrent workers without race conditions.
    """
    return add_messages(left, right)

class ConcurrencyManager:
    """
    Manages Optimistic Concurrency Control (OCC) and Branch Merge Escalations.
    """
    def __init__(self):
        # We track checkpoint IDs to implement OCC logic externally if needed,
        # though LangGraph PostgresSaver natively handles some of this.
        self.latest_checkpoints = {}

    def verify_occ(self, session_id: str, provided_checkpoint_id: str) -> bool:
        """
        Optimistic Concurrency Control (OCC) for asynchronous human/agent clashes.
        If a human tries to edit the graph state based on a stale view, we reject it.
        """
        current_checkpoint = self.latest_checkpoints.get(session_id)
        if current_checkpoint and current_checkpoint != provided_checkpoint_id:
            logger.warning(f"OCC Collision detected for session {session_id}. Human has stale view.")
            return False
        return True

    def update_checkpoint(self, session_id: str, checkpoint_id: str):
        self.latest_checkpoints[session_id] = checkpoint_id

    @staticmethod
    def escalate_merge_conflict(conflict_details: str):
        """
        Triggered by the True Git Backend if `git merge` or `git rebase` fails.
        Raises a GraphInterrupt which suspends the LangGraph execution and routes
        to the Human Supervisor for manual resolution via the Cloud IDE.
        """
        logger.error(f"Merge conflict detected! Escalating to human supervisor: {conflict_details}")
        raise GraphInterrupt(f"GIT_MERGE_CONFLICT: {conflict_details}")

# Singleton instance
concurrency_manager = ConcurrencyManager()
