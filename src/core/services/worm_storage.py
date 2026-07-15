import logging
from src.core.ontology import EpistemicQuarantineSnapshot
from src.core.db import get_db_pool

logger = logging.getLogger(__name__)

async def persist_quarantine_snapshot(snapshot: EpistemicQuarantineSnapshot) -> None:
    """
    Persists an epistemic quarantine snapshot to WORM storage (Postgres).
    Abstracts infrastructure logic away from the Brain.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO epistemic_quarantine_snapshots (snapshot_id, raw_payload) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                snapshot.snapshot_id, snapshot.raw_payload
            )
    except Exception as e:
        logger.warning(f"Failed to persist transcript to WORM: {e}")
