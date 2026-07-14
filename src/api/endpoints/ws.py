from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from src.core.vfs.crdt_sync import crdt_manager
from src.core.vfs.terminal_tty import tty_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/crdt/{document_id}")
async def crdt_endpoint(websocket: WebSocket, document_id: str):
    """
    CRDT WebSocket endpoint for Yjs/Automerge IDE syncing.
    """
    await crdt_manager.connect_client(document_id, websocket)
    try:
        while True:
            data = await websocket.receive_bytes()
            await crdt_manager.broadcast_update(document_id, data, sender=websocket)
    except WebSocketDisconnect:
        await crdt_manager.disconnect_client(document_id, websocket)

@router.websocket("/tty/{session_id}")
async def tty_endpoint(websocket: WebSocket, session_id: str):
    """
    TTY WebSocket endpoint for xterm.js to attach to the shared tmux session.
    """
    await tty_manager.attach_client(session_id, websocket)

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
            # Command to trigger a time-travel rewind or stream state
            data = await websocket.receive_json()
            if data.get("action") == "rewind":
                logger.info(f"Time-Travel Rewind requested to checkpoint {data.get('checkpoint_id')}")
                # LangGraph checkpoint restore logic would go here
    except WebSocketDisconnect:
        logger.info(f"State Sync disconnected for session {session_id}")
