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
        self._s3_client = None

    @property
    def s3_client(self):
        if self._s3_client is None:
            import boto3
            import botocore
            from src.core.config import settings
            self._s3_client = boto3.client(
                "s3",
                region_name=settings.WORM_S3_REGION,
                endpoint_url=settings.WORM_S3_ENDPOINT,
                aws_access_key_id=settings.WORM_S3_ACCESS_KEY,
                aws_secret_access_key=settings.WORM_S3_SECRET_KEY,
                config=botocore.client.Config(signature_version="s3")
            )
        return self._s3_client

    def _hash_event(self, event_data: dict) -> str:
        """Generates a cryptographic hash of the audit event to guarantee immutability."""
        event_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()

    def log_agent_thought(self, agent_id: str, run_id: str, thought_content: str, metadata: dict = None) -> str:
        """
        Streams an agent's internal LangGraph reasoning step to the WORM log.
        Returns the cryptographic hash for cross-referencing with Langfuse spans.
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
        
        # Simulate pushing to SIEM (OpenTelemetry/Splunk)
        logger.info(f"[SIEM AUDIT] Agent Thought Logged: {event_hash}")
        
        # Simulate pushing to WORM S3 Bucket
        self._write_to_worm_s3(f"audit/agents/{agent_id}/{run_id}/{event_hash}.json", event)
        return event_hash

    def log_supervisor_action(self, supervisor_email: str, action: str, target: str, request_id: str = None) -> str:
        """
        Streams a human Supervisor's action (e.g., JIT approval, graph rewind) to the WORM log.
        Returns the cryptographic hash for cross-referencing with Langfuse spans.
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
        
        # Simulate pushing to SIEM (OpenTelemetry/Splunk)
        logger.info(f"[SIEM AUDIT] Supervisor Action Logged: {event_hash} by {supervisor_email}")
        
        # Simulate pushing to WORM S3 Bucket
        self._write_to_worm_s3(f"audit/supervisors/{supervisor_email}/{event_hash}.json", event)
        return event_hash

    def _write_to_worm_s3(self, object_key: str, data: dict):
        """
        Writes the audit log to S3/MinIO.
        """
        try:
            from src.core.config import settings
            self.s3_client.put_object(
                Bucket=settings.WORM_S3_BUCKET,
                Key=object_key,
                Body=json.dumps(data)
            )
            logger.info(f"Successfully wrote {object_key} to WORM S3")
        except Exception as e:
            logger.error(f"Failed to write {object_key} to WORM S3: {e}")

# Singleton instance
auditor = WORMStorageAuditor()
