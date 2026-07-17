import json
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class WORMStorageAuditor:
    """
    WORM (Write Once Read Many) Storage & OpenTelemetry SIEM Auditing.
    Enforces CISO requirement: Every agent thought and human approval MUST be 
    cryptographically hashed and streamed to WORM S3 buckets, and pushed to the SIEM.
    """
    def __init__(self):
        # In a real environment, this initializes the AWS S3/MinIO client configured for Object Lock (WORM).
        self.worm_bucket = "coreason-audit-worm"
        
    def _hash_event(self, event_data: dict) -> str:
        """Generates a cryptographic hash of the audit event to guarantee immutability."""
        event_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()

    def log_agent_thought(self, agent_id: str, run_id: str, thought_content: str, metadata: dict = None) -> str:
        """
        Streams an agent's internal LangGraph reasoning step to the WORM log.
        Returns the cryptographic hash for cross-referencing with LangSmith spans.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "AGENT_THOUGHT",
            "agent_id": agent_id,
            "run_id": run_id,
            "content": thought_content,
            "metadata": metadata or {}
        }
        event_hash = self._hash_event(event)
        event["hash"] = event_hash
        
        # Simulate pushing to SIEM (OpenTelemetry OTLP Collector)
        logger.info(f"[SIEM AUDIT] Agent Thought Logged: {event_hash}")
        
        # Simulate pushing to WORM S3 Bucket
        self._write_to_worm_s3(f"audit/agents/{agent_id}/{run_id}/{event_hash}.json", event)
        return event_hash

    def log_supervisor_action(self, supervisor_email: str, action: str, target: str, request_id: str = None) -> str:
        """
        Streams a human Supervisor's action (e.g., JIT approval, graph rewind) to the WORM log.
        Returns the cryptographic hash for cross-referencing with LangSmith spans.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "SUPERVISOR_ACTION",
            "supervisor": supervisor_email,
            "action": action,
            "target": target,
            "request_id": request_id
        }
        event_hash = self._hash_event(event)
        event["hash"] = event_hash
        
        # Simulate pushing to SIEM (OpenTelemetry OTLP Collector)
        logger.info(f"[SIEM AUDIT] Supervisor Action Logged: {event_hash} by {supervisor_email}")
        
        # Simulate pushing to WORM S3 Bucket
        self._write_to_worm_s3(f"audit/supervisors/{supervisor_email}/{event_hash}.json", event)
        return event_hash

    def _write_to_worm_s3(self, object_key: str, data: dict):
        """
        Placeholder for the actual boto3 S3 put_object call with Object Lock retention parameters.
        """
        # s3_client.put_object(Bucket=self.worm_bucket, Key=object_key, Body=json.dumps(data), ...)
        logger.info(f"Simulating WORM S3 write for {object_key}")

# Singleton instance
auditor = WORMStorageAuditor()
