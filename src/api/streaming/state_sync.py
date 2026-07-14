"""
State Sync WebSocket — Real-time LangGraph state updates and time-travel debugging.
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/state/{session_id}")
async def state_sync_endpoint(websocket: WebSocket, session_id: str):
    """
    Real-Time Multiplayer State Sync and Time-Travel Debugging.
    Streams LangGraph Postgres state updates to the UI.
    """
    await websocket.accept()
    logger.info(f"State Sync connected for session {session_id}")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "rewind":
                logger.info(f"Time-Travel Rewind requested to checkpoint {data.get('checkpoint_id')}")
                # LangGraph checkpoint restore logic would go here
                await websocket.send_json({
                    "status": "rewinding",
                    "checkpoint_id": data.get("checkpoint_id"),
                })
    except WebSocketDisconnect:
        logger.info(f"State Sync disconnected for session {session_id}")
