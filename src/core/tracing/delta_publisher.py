# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: src.core.ontology
import json
import logging
from typing import Dict, Any

import jsonpatch
from src.core.ws_backplane import pubsub_backplane

logger = logging.getLogger(__name__)

class StateDeltaPublisher:
    """
    State Delta Publisher for LangGraph State Sync.
    Stores the previous state and computes RFC 6902 JSON Patches to dramatically
    reduce WebSocket payload size for long-running reasoning chains.
    """
    def __init__(self):
        # Maps session_id -> previous state dict
        self.previous_states: Dict[str, Dict[str, Any]] = {}

    async def publish_update(self, session_id: str, new_state: Dict[str, Any]):
        """
        Publishes the state update for the given session to the Redis backplane.
        If a previous state exists, it broadcasts a JSON patch.
        Otherwise, it broadcasts the full state.
        """
        channel = f"agent_progress:{session_id}"
        
        # If we have no prior state, broadcast full
        if session_id not in self.previous_states:
            payload = {
                "type": "full_state",
                "data": new_state
            }
            logger.debug(f"Publishing full state to {channel}")
        else:
            old_state = self.previous_states[session_id]
            patch = jsonpatch.make_patch(old_state, new_state)
            
            # If no change, skip publishing
            if not patch.patch:
                logger.debug(f"No state change for {channel}, skipping broadcast.")
                return
                
            payload = {
                "type": "delta",
                "patch": patch.patch
            }
            logger.debug(f"Publishing JSON patch to {channel} (operations: {len(patch.patch)})")
        
        # Update the memory
        self.previous_states[session_id] = new_state
        
        # Publish
        await pubsub_backplane.publish(channel, json.dumps(payload))

    def clear_session(self, session_id: str):
        """
        Clears the tracked state for a session to prevent memory leaks.
        """
        if session_id in self.previous_states:
            del self.previous_states[session_id]

# Singleton instance
state_delta_publisher = StateDeltaPublisher()
