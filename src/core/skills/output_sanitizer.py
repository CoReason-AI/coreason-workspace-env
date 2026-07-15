import logging
from langchain_core.tools import tool
from src.agents.output_sanitizer.orchestrator import OutputSanitizerAgent

logger = logging.getLogger(__name__)

@tool
def sanitize_json_output(raw_json_string: str) -> str:
    """
    Delegates to the OutputSanitizer Sub-Agent to strictly format noisy strings into Markdown.
    """
    logger.info("Delegating to OutputSanitizerAgent.")
    sanitizer = OutputSanitizerAgent()
    return sanitizer.execute(raw_json_string, session_id="sanitization_task")
