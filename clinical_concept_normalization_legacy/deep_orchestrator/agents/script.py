from typing import Callable, Any
from langchain_core.messages import AIMessage
from ..state import GlobalSwarmState

def build_script_node(name: str, func: Callable[[GlobalSwarmState], dict | str], backend: Any = None):
    """Wraps a pure Python function to act as a LangGraph node.
    
    This factory bridges non-LLM scripts into the LangGraph network, automatically
    formatting their outputs so peer Reasoning Agents can interpret them.
    """
    
    def node_function(state: GlobalSwarmState) -> dict:
        # Evaluate the deterministic script
        result = func(state)
        
        # Ensure the output conforms to LangGraph message formatting
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
        else:
            messages = [AIMessage(content=str(result), name=name)]
            
        return {
            "messages": messages,
            "sender": name
        }
    
    return node_function
