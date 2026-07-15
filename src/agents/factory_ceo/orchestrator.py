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

from src.core.db import get_db_pool

async def epistemic_interceptor_node(state: dict[str, Any]) -> dict[str, Any]:
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
        
        # Persist to WORM Postgres table for enterprise statelessness using global pool
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO epistemic_quarantine_snapshots (snapshot_id, raw_payload) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    snapshot.snapshot_id, snapshot.raw_payload
                )
        except Exception as e:
            # WORM persistence is mandatory for security compliance. Fail closed.
            raise RuntimeError(f"Epistemic Interceptor failed to quarantine transcript: {e}")
        
        proxy = EpistemicProxyState(
            proxy_cid=snapshot.snapshot_id,
            structural_type="HumanTranscript"
        )
        
        return {
            "raw_transcript": None,
            "epistemic_proxy": proxy
        }
        
    return {}
