from ..state import GlobalSwarmState

def supervisor_router(state: GlobalSwarmState) -> str:
    """Routes to the next agent based on the 'next_agent' state field.
    
    If no agent is designated or the designated agent is FINISH, execution halts.
    """
    next_agent = state.get("next_agent")
    
    if not next_agent or next_agent == "FINISH":
        return "__end__"
        
    return next_agent
