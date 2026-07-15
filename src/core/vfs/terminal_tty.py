import logging
import asyncio
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class SharedTTYMultiplexer:
    """
    Shared Collaborative TTY Multiplexing (tmux).
    Bridges the xterm.js frontend to an ephemeral OpenShell sandbox running tmux.
    Allows agents and humans to share the exact same CLI session simultaneously.
    """
    def __init__(self):
        # Maps a Project session ID to a tmux socket/session
        self.active_sessions = {}

    async def attach_client(self, session_id: str, websocket: WebSocket):
        """
        Attaches a WebSocket client (human browser) to the shared tmux session.
        """
        await websocket.accept()
        logger.info(f"Human attached to Shared TTY for session: {session_id}")
        
        # Simulated connection to the OpenShell Gateway running `ttyd` and `tmux`
        # In reality, this proxies the WebSocket frames to the Kubernetes pod's ttyd port.
        try:
            while True:
                # Receive keystrokes from xterm.js
                data = await websocket.receive_text()
                
                # Forward to tmux (simulated)
                # await self._forward_to_tmux(session_id, data)
                
                # Echo back to xterm.js (simulated PTY response)
                # await websocket.send_text(data)
                pass
        except Exception as e:
            logger.error(f"TTY WebSocket closed: {e}")
        finally:
            logger.info(f"Cleaning up interactive OpenShell session: {session_id}")
            self._cleanup_session(session_id)
            
    def _cleanup_session(self, session_id: str):
        """
        Terminates the LangGraph process trees and supervisor processes associated with the closed interactive OpenShell session.
        This prevents resource leaks (Issue #6720).
        """
        logger.info(f"Terminating LangGraph servers and supervisor processes for session {session_id}")
        # Placeholder for actual process termination logic
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
    async def inject_agent_command(self, session_id: str, command: str):
        """
        Allows a LangGraph agent to type a command directly into the shared tmux session.
        The human can watch the characters appear live on their xterm.js UI.
        """
        logger.info(f"Agent injecting command into TTY {session_id}: {command}")
        # simulated: tmux send-keys -t {session_id} "{command}" C-m

# Singleton instance
tty_manager = SharedTTYMultiplexer()
