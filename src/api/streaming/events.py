from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

async def langgraph_event_generator(session_id: str):
    """
    Subscribes to LangGraph's astream_events for the Accordion UX via Postgres LISTEN.
    """
    import asyncio
    from src.core.db import get_db_pool
    
    queue = asyncio.Queue()
    
    def notification_handler(connection, pid, channel, payload):
        queue.put_nowait(payload)
        
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            channel_name = f"langgraph_events_{session_id}"
            await conn.add_listener(channel_name, notification_handler)
            yield f"data: {json.dumps({'event': 'stream_connected', 'session': session_id})}\n\n"
            
            while True:
                payload = await queue.get()
                yield f"data: {payload}\n\n"
    except asyncio.CancelledError:
        # Connection closed by client
        pass
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("SSE stream error for session %s: %s", session_id, e)
        yield f"data: {json.dumps({'error': 'Internal stream error'})}\n\n"


@router.get("/api/v2/agents/{agent_name}/stream")
async def stream_agent_events(agent_name: str, session_id: str = "default"):
    """
    SSE endpoint for streaming LangGraph tracker tasks in real-time.
    """
    return StreamingResponse(langgraph_event_generator(session_id), media_type="text/event-stream")
