"""
LangSmith/WORM Tracing Bridge — dual-write tracing with shared run_id and hash.

This bridge pattern ensures:
1. Every agent thought is traced in LangSmith for visual debugging
2. Every agent thought is cryptographically hashed and written to WORM S3
3. Both systems share the same run_id and hash for cross-referencing

Usage:
    from src.core.tracing import TracingBridge

    bridge = TracingBridge()
    bridge.trace_agent_thought(agent_id="factory_ceo", run_id="abc-123", thought="Planning...")
"""
import logging
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TracingBridge:
    """
    Dual-write bridge between LangSmith (visual tracing) and WORM (cryptographic audit).
    Both systems share the same run_id and cryptographic hash.
    """

    def __init__(self):
        self._langsmith_client = None
        self._auditor = None

    @property
    def langsmith_client(self):
        """Lazy-initialize the LangSmith client."""
        if self._langsmith_client is None:
            try:
                from langsmith import Client
                from src.core.tracing.config import langsmith_config
                
                if langsmith_config.is_configured:
                    self._langsmith_client = Client(
                        api_url=langsmith_config.endpoint,
                        api_key=langsmith_config.api_key
                    )
                    logger.info(f"LangSmith client initialized: {langsmith_config.endpoint}")
                else:
                    logger.info("LangSmith not configured — tracing to WORM only")
            except ImportError:
                logger.warning("langsmith package not installed — tracing to WORM only")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith: {e}")
        return self._langsmith_client

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
        Dual-write an agent thought to both LangSmith and WORM.

        Returns:
            Dict with 'hash' and optionally 'langsmith_run_id'.
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

        # 2. Write to LangSmith — attach the WORM hash as metadata
        if self.langsmith_client:
            try:
                from langsmith import RunTree
                from src.core.tracing.config import langsmith_config
                
                rt = RunTree(
                    name=f"agent_thought:{agent_id}",
                    run_type="chain",
                    inputs={"thought": thought},
                    project_name=langsmith_config.project,
                    id=uuid.UUID(run_id) if len(run_id) == 36 else None,
                    extra={"metadata": {"worm_hash": worm_hash, **(metadata or {})}}
                )
                rt.end(outputs={"status": "traced"})
                rt.post()
                result["langsmith_run_id"] = str(rt.id)
            except Exception as e:
                logger.warning(f"LangSmith trace creation failed: {e}")

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
        Dual-write a supervisor action to both LangSmith and WORM.
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

        # 2. Write to LangSmith
        if self.langsmith_client:
            try:
                from langsmith import RunTree
                from src.core.tracing.config import langsmith_config
                
                rt = RunTree(
                    name=f"supervisor_action:{supervisor_email}",
                    run_type="chain",
                    inputs={
                        "action": action,
                        "target": target,
                        "request_id": request_id,
                    },
                    project_name=langsmith_config.project,
                    id=uuid.UUID(effective_run_id) if len(effective_run_id) == 36 else None,
                    extra={"metadata": {"worm_hash": worm_hash}}
                )
                rt.end(outputs={"status": "traced"})
                rt.post()
                result["langsmith_run_id"] = str(rt.id)
            except Exception as e:
                logger.warning(f"LangSmith trace creation failed: {e}")

        return result

    def flush(self):
        """Flush any pending events (No-op for basic LangSmith RunTree but kept for interface compatibility)."""
        pass


# Singleton
tracing_bridge = TracingBridge()
