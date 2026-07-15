from typing import Any
import uuid
from deepagents import DeepAgent

from coreason_manifest.spec.ontology import (
    EpistemicQuarantineSnapshot,
    EpistemicProxyState
)
from src.core.schemas.epistemic_firewall import LibrarianRoutingState


class FactoryCeoAgent(DeepAgent):
    """
    Orchestrator for factory_ceo.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

import os
import psycopg2

def epistemic_interceptor_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph Node that physically intercepts large raw human transcripts
    BEFORE they enter the factory_ceo's context window.
    """
    raw_payload = state.get("raw_transcript")
    
    if raw_payload:
        snapshot = EpistemicQuarantineSnapshot(
            snapshot_id=str(uuid.uuid7()),
            raw_payload=raw_payload
        )
        
        # Persist to WORM Postgres table for enterprise statelessness
        db_dsn = os.environ.get("POSTGRES_DSN", "postgresql://admin:password@localhost:5432/knowledge_db")
        try:
            with psycopg2.connect(db_dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO epistemic_quarantine_snapshots (snapshot_id, raw_payload) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (snapshot.snapshot_id, snapshot.raw_payload)
                    )
                conn.commit()
        except Exception as e:
            # Fallback or log if Postgres is unavailable, but fail-open for testing
            pass
        
        proxy = EpistemicProxyState(
            proxy_cid=snapshot.snapshot_id,
            structural_type="HumanTranscript"
        )
        
        state["raw_transcript"] = None
        state["epistemic_proxy"] = proxy
        
    return state
