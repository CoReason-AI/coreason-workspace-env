import logging
import uuid
from typing import Annotated
from langchain_core.tools import tool
from langgraph.store.base import BaseStore
from langgraph.prebuilt import InjectedStore

logger = logging.getLogger(__name__)

@tool
async def log_structural_failure(
    code_snippet: str, 
    error_message: str, 
    resolution_hints: str,
    store: Annotated[BaseStore, InjectedStore()]
) -> str:
    """
    Logs a structural failure (e.g., AST parse error, Pydantic validation error) into the localized RAG memory.
    Use this when an artifact fails deterministic validation to ensure the failure context is saved.
    """
    try:
        content = (
            f"ERROR:\n{error_message}\n\n"
            f"CODE:\n{code_snippet}\n\n"
            f"HINTS:\n{resolution_hints}"
        )
        # Store under the namespace ("failures", "structural")
        await store.aput(("failures", "structural"), str(uuid.uuid4()), {"content": content})
        return "Successfully logged structural failure to localized Postgres memory."
    except Exception as e:
        logger.error(f"Failed to log failure: {e}")
        return f"Error logging failure: {e}"

@tool
async def recall_past_failures(
    context_query: str,
    store: Annotated[BaseStore, InjectedStore()]
) -> str:
    """
    Recalls past structural failures from the localized Postgres RAG memory.
    Use this tool before validating or generating new code to check for historical gotchas and avoid repeating mistakes.
    Pass in a query describing the context, such as the name of the function or the type of error you suspect.
    """
    try:
        # Perform semantic search natively in the Store API
        results = await store.asearch(("failures", "structural"), query=context_query, limit=3)
        
        if not results:
            return "No relevant past failures found in local memory."
            
        formatted_results = "### PAST FAILURES (Do not repeat these):\n\n"
        for i, r in enumerate(results):
            formatted_results += f"#### Failure {i+1}:\n{r.value.get('content', '')}\n\n"
            
        return formatted_results
    except Exception as e:
        logger.error(f"Failed to recall failures: {e}")
        return f"Error recalling failures: {e}"
