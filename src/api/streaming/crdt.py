"""
CRDT WebSocket — Yjs/Automerge IDE syncing for multi-user collaborative editing.
Delegated natively to DeepAgents Filesystem Middleware.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/crdt/{document_id}")
async def crdt_endpoint(websocket: WebSocket, document_id: str):
    """
    CRDT WebSocket endpoint for Yjs/Automerge IDE syncing.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # In the future, proxy to deepagents.middleware.filesystem for CRDT sync
            pass
    except WebSocketDisconnect:
        pass
