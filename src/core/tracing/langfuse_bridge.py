"""
Langfuse/WORM Tracing Bridge — dual-write tracing with shared run_id and hash.

This bridge pattern ensures:
1. Every agent thought is traced in Langfuse for visual debugging
2. Every agent thought is cryptographically hashed and written to WORM S3
3. Both systems share the same run_id and hash for cross-referencing

Usage:
    from src.core.tracing import TracingBridge

    bridge = TracingBridge()
    bridge.trace_agent_thought(agent_id="factory_ceo", run_id="abc-123", thought="Planning...")
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TracingBridge:
    """
    Dual-write bridge between Langfuse (visual tracing) and WORM (cryptographic audit).
    Both systems share the same run_id and cryptographic hash.
    """

    def __init__(self):
        self._langfuse = None
        self._auditor = None

    @property
    def langfuse(self):
        """Lazy-initialize the Langfuse client."""
        if self._langfuse is None:
            try:
                from langfuse import Langfuse
                from src.core.tracing.config import langfuse_config

                if langfuse_config.enabled and langfuse_config.is_configured:
                    self._langfuse = Langfuse(
                        host=langfuse_config.host,
                        public_key=langfuse_config.public_key,
                        secret_key=langfuse_config.secret_key,
                    )
                    logger.info(f"Langfuse client initialized: {langfuse_config.host}")
                else:
                    logger.info("Langfuse disabled or not configured — tracing to WORM only")
            except ImportError:
                logger.warning("langfuse package not installed — tracing to WORM only")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
        return self._langfuse

    @property
    def auditor(self):
        """Lazy-initialize the WORM auditor."""
        if self._auditor is None:
            from src.core.security.audit import auditor
            self._auditor = auditor
        return self._auditor

    def trace_agent_thought(
        self,
        agent_id: str,
        run_id: str,
        thought: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Dual-write an agent thought to both Langfuse and WORM.

        Returns:
            Dict with 'hash' and optionally 'langfuse_span_id'.
        """
        result = {}

        # 1. Write to WORM auditor — get the cryptographic hash
        worm_hash = self.auditor.log_agent_thought(
            agent_id=agent_id,
            run_id=run_id,
            thought_content=thought,
            metadata=metadata,
        )
        result["hash"] = worm_hash or ""

        # 2. Write to Langfuse — attach the WORM hash as a span attribute
        if self.langfuse:
            try:
                trace = self.langfuse.trace(
                    id=run_id,
                    name=f"agent:{agent_id}",
                    metadata={"worm_hash": worm_hash, **(metadata or {})},
                )
                span = trace.span(
                    name="agent_thought",
                    input={"thought": thought},
                    metadata={
                        "worm_hash": worm_hash,
                        "agent_id": agent_id,
                    },
                )
                span.end()
                result["langfuse_span_id"] = span.id if hasattr(span, "id") else ""
            except Exception as e:
                logger.warning(f"Langfuse span creation failed: {e}")

        return result

    def trace_supervisor_action(
        self,
        supervisor_email: str,
        action: str,
        target: str,
        request_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Dual-write a supervisor action to both Langfuse and WORM.
        """
        result = {}
        effective_run_id = run_id or str(uuid.uuid7())

        # 1. Write to WORM
        worm_hash = self.auditor.log_supervisor_action(
            supervisor_email=supervisor_email,
            action=action,
            target=target,
            request_id=request_id,
        )
        result["hash"] = worm_hash or ""

        # 2. Write to Langfuse
        if self.langfuse:
            try:
                trace = self.langfuse.trace(
                    id=effective_run_id,
                    name=f"supervisor:{supervisor_email}",
                    metadata={"worm_hash": worm_hash},
                )
                span = trace.span(
                    name="supervisor_action",
                    input={
                        "action": action,
                        "target": target,
                        "request_id": request_id,
                    },
                    metadata={"worm_hash": worm_hash},
                )
                span.end()
                result["langfuse_span_id"] = span.id if hasattr(span, "id") else ""
            except Exception as e:
                logger.warning(f"Langfuse span creation failed: {e}")

        return result

    def flush(self):
        """Flush any pending Langfuse events."""
        if self.langfuse:
            try:
                self.langfuse.flush()
            except Exception:
                pass


# Singleton
tracing_bridge = TracingBridge()
