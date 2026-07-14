from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool
def escalate_to_human(question_or_issue: str) -> str:
    """
    Use this tool when a strategic decision is ambiguous or falls outside your domain of confidence.
    This tool triggers a LangGraph interrupt, pausing the autonomous execution and surfacing the
    question to the Human counterpart (e.g. Human CEO or Human PM).
    
    The graph will go to sleep and persist its state in Postgres until the human responds.
    Once the human responds, the execution will resume and this tool will return the human's answer.
    """
    logger.info(f"🚨 AGENT ESCALATION TRIGGERED: {question_or_issue}")
    
    # In a true LangGraph setup, raising a specific exception or returning a specific state 
    # flag here instructs the orchestrator to break and hit `interrupt_before`.
    # For now, we simulate the interrupt mechanism:
    
    # MAGIC STRING: When the LangGraph executor sees this prefix, it yields execution back to the client.
    return f"__INTERRUPT_REQUIRED__: {question_or_issue}"
