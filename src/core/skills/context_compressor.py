import logging
from langchain_core.tools import tool
from src.agents.context_compressor.orchestrator import ContextCompressorAgent

logger = logging.getLogger(__name__)

@tool
def compress_context(raw_payload: str, compression_goal: str) -> str:
    """
    Compresses a massive raw payload into a high-signal summary by delegating to the ContextCompressor Sub-Agent.
    """
    logger.info(f"Delegating compression of length {len(raw_payload)} to ContextCompressorAgent with goal: {compression_goal}")
    
    if len(raw_payload) < 500:
        return raw_payload # No need to compress small payloads
        
    compressor = ContextCompressorAgent()
    return compressor.execute(raw_payload, compression_goal, session_id="compression_task")
