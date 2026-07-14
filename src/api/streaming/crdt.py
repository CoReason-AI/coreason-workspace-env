"""
CRDT WebSocket — Yjs/Automerge IDE syncing for multi-user collaborative editing.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.vfs.crdt_sync import crdt_manager

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
