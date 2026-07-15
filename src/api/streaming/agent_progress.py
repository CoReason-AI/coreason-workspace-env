"""
Agent Progress WebSocket — streams real-time agent execution progress.
Enables CLI, SDK, and MCP surfaces to subscribe to execution streams.
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.ws_backplane import pubsub_backplane

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/agent-progress/{job_id}")
async def agent_progress_endpoint(websocket: WebSocket, job_id: str):
    """
    Streams real-time progress of an agent execution.
    Subscribes to the Redis Pub/Sub channel for the given job_id.
    """
    await websocket.accept()
    logger.info(f"Agent progress stream connected for job {job_id}")

    channel = f"agent_progress:{job_id}"

    async def on_message(message: str):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.debug("WebSocket client disconnected: %s", e)

    await pubsub_backplane.subscribe(channel, on_message)

    try:
        while True:
            # Keep the connection alive — client can also send control messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        await pubsub_backplane.unsubscribe(channel, on_message)
        logger.info(f"Agent progress stream disconnected for job {job_id}")
