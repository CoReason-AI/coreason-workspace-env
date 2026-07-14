import logging
import asyncio
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class CRDTSyncManager:
    """
    CRDT (Conflict-Free Replicated Data Type) Sync Manager.
    Handles the backend synchronization of Yjs/Automerge documents for the Cloud IDE.
    Allows agents and humans to type in the exact same file simultaneously without collisions.
    """
    def __init__(self):
        # Maps a document/file path to a list of connected WebSockets
        self.active_documents: Dict[str, list[WebSocket]] = {}
        
        # In a real environment, this connects to a Yjs Redis persistence layer 
        # (e.g. y-redis) to horizontally scale the CRDT state across FastAPI nodes.
        self.redis_crdt_backend = "redis://..."

    async def connect_client(self, document_id: str, websocket: WebSocket):
        """Registers a new IDE client (human or agent) to a CRDT document stream."""
        await websocket.accept()
        if document_id not in self.active_documents:
            self.active_documents[document_id] = []
        self.active_documents[document_id].append(websocket)
        logger.info(f"Client connected to CRDT document: {document_id}")

    async def disconnect_client(self, document_id: str, websocket: WebSocket):
        """Removes a client from the CRDT document stream."""
        if document_id in self.active_documents:
            self.active_documents[document_id].remove(websocket)
            if not self.active_documents[document_id]:
                del self.active_documents[document_id]
        logger.info(f"Client disconnected from CRDT document: {document_id}")

    async def broadcast_update(self, document_id: str, update_data: bytes, sender: WebSocket = None):
        """
        Broadcasts a Yjs binary update vector to all other connected clients.
        """
        if document_id in self.active_documents:
            for client in self.active_documents[document_id]:
                if client != sender:
                    try:
                        await client.send_bytes(update_data)
                    except Exception as e:
                        logger.error(f"Failed to send CRDT update to client: {e}")

# Singleton instance
crdt_manager = CRDTSyncManager()
