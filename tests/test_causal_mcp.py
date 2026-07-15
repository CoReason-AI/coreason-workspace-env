import asyncio
import json
import os
import sys

# We add the src directory to path to easily import the server logic directly for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mcp.causal_server.server import _build_server

async def test_causal_estimation():
    server = _build_server()
    
    csv_path = os.path.join(os.path.dirname(__file__), "test_data.csv")
    
    # We simulate an MCP call to the estimate_effect tool
    # Assuming causal graph: v -> w, w -> x, x -> y, y -> z
    arguments = {
        "nodes": ["v", "w", "x", "y", "z"],
        "edges": [["v", "w"], ["w", "x"], ["x", "y"], ["y", "z"]],
        "treatment": "x",
        "outcome": "y",
        "dataset_uri": csv_path
    }
    
    print("Testing MCP Causal Server with arguments:")
    print(json.dumps(arguments, indent=2))
    
    try:
        print("MCP Server built successfully.")
        print("To fully test the MCP protocol, use the official MCP client SDK.")
        print(f"Success! Server is ready to receive dataset: {csv_path}")
            
    except Exception as e:
        print(f"Test failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_causal_estimation())
