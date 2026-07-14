"""
TTY WebSocket — xterm.js terminal attachment to shared tmux sessions.
"""
from fastapi import APIRouter, WebSocket

from src.core.vfs.terminal_tty import tty_manager

router = APIRouter()


@router.websocket("/tty/{session_id}")
async def tty_endpoint(websocket: WebSocket, session_id: str):
    """
    TTY WebSocket endpoint for xterm.js to attach to the shared tmux session.
    """
    await tty_manager.attach_client(session_id, websocket)
