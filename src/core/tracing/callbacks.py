"""
LangChain/LangGraph Callback Handler — hooks into execution lifecycle for tracing.

Integrates with the TracingBridge to create Langfuse spans and WORM audit entries
for every LLM call, tool call, and chain execution.

Usage:
    from src.core.tracing.callbacks import CoReasonTracingCallback

    callback = CoReasonTracingCallback(run_id="abc-123", agent_id="factory_ceo")
    # Pass to LangGraph execution as a callback
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class CoReasonTracingCallback(BaseCallbackHandler):
    """
    LangChain callback that bridges LangGraph execution events
    to both Langfuse (visual tracing) and WORM (cryptographic audit).
    """

    def __init__(self, run_id: str, agent_id: str):
        super().__init__()
        self.run_id = run_id
        self.agent_id = agent_id
        self._bridge = None

    @property
    def bridge(self):
        if self._bridge is None:
            from src.core.tracing.langfuse_bridge import tracing_bridge
            self._bridge = tracing_bridge
        return self._bridge

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM starts generating."""
        model_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        self.bridge.trace_agent_thought(
            agent_id=self.agent_id,
            run_id=self.run_id,
            thought=f"[LLM_START] Model: {model_name}, Prompts: {len(prompts)}",
            metadata={
                "event": "llm_start",
                "model": model_name,
                "prompt_count": len(prompts),
                "langchain_run_id": str(run_id) if run_id else None,
            },
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM finishes generating."""
        generation_count = sum(len(g) for g in response.generations)
        self.bridge.trace_agent_thought(
            agent_id=self.agent_id,
            run_id=self.run_id,
            thought=f"[LLM_END] Generations: {generation_count}",
            metadata={
                "event": "llm_end",
                "generation_count": generation_count,
                "langchain_run_id": str(run_id) if run_id else None,
            },
        )

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts executing."""
        tool_name = serialized.get("name", "unknown")
        self.bridge.trace_agent_thought(
            agent_id=self.agent_id,
            run_id=self.run_id,
            thought=f"[TOOL_START] Tool: {tool_name}",
            metadata={
                "event": "tool_start",
                "tool_name": tool_name,
                "langchain_run_id": str(run_id) if run_id else None,
            },
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes executing."""
        self.bridge.trace_agent_thought(
            agent_id=self.agent_id,
            run_id=self.run_id,
            thought=f"[TOOL_END] Output length: {len(output)}",
            metadata={
                "event": "tool_end",
                "output_length": len(output),
                "langchain_run_id": str(run_id) if run_id else None,
            },
        )

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chain/graph finishes execution."""
        self.bridge.trace_agent_thought(
            agent_id=self.agent_id,
            run_id=self.run_id,
            thought=f"[CHAIN_END] Output keys: {list(outputs.keys()) if isinstance(outputs, dict) else 'non-dict'}",
            metadata={
                "event": "chain_end",
                "langchain_run_id": str(run_id) if run_id else None,
            },
        )
        # Flush to ensure all traces are sent
        self.bridge.flush()
