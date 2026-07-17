import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.core.db import get_db_pool

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/api/v2/agents/{agent_name}/ws")
async def agent_websocket(websocket: WebSocket, agent_name: str, session_id: str):
    """
    WebSocket endpoint for bi-directional communication with the running LangGraph agent.
    Streams execution events via Postgres LISTEN, and forwards human responses via NOTIFY.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for agent {agent_name}, session {session_id}")
    
    pool = await get_db_pool()
    channel_name = f"langgraph_events_{session_id}"
    response_channel = f"human_response_{session_id}"
    
    # We need a queue to bridge the Postgres listener callback into the async loop
    queue = asyncio.Queue()
    
    def notification_handler(connection, pid, channel, payload):
        queue.put_nowait(payload)
        
    async with pool.acquire() as conn:
        try:
            await conn.add_listener(channel_name, notification_handler)
            await websocket.send_text(json.dumps({'event': 'stream_connected', 'session': session_id}))
            
            # Create two tasks: one for reading from Postgres (and sending to WS),
            # and one for reading from WS (and sending to Postgres/Agent)
            
            async def read_from_pg():
                while True:
                    payload = await queue.get()
                    await websocket.send_text(payload)
            
            async def read_from_ws():
                while True:
                    data = await websocket.receive_text()
                    # User responded to an interrupt. Forward this response so the graph can resume.
                    # We broadcast it on a response channel that the orchestrator will listen to.
                    await conn.execute(f"SELECT pg_notify($1, $2)", response_channel, data)
            
            pg_task = asyncio.create_task(read_from_pg())
            ws_task = asyncio.create_task(read_from_ws())
            
            done, pending = await asyncio.wait(
                [pg_task, ws_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for p in pending:
                p.cancel()
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected.")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await conn.remove_listener(channel_name, notification_handler)
