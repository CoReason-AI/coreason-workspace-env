import json
import logging
import asyncio
import sys
import os
from typing import Any
from mcp.server.stdio import stdio_server
from mcp.server import Server

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import dowhy
    from dowhy import CausalModel
except ImportError:
    dowhy = None

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger("causal_server")

def _build_server() -> Server:
    server = Server("coreason-causal-inference")

    @server.list_tools()
    async def handle_list_tools() -> list:
        return [
            {
                "name": "mcp_causal_server_estimate_effect",
                "description": "Calculates the formal causal effect (ATE) using DoWhy and a directed acyclic graph.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodes": {"type": "array", "items": {"type": "string"}},
                        "edges": {
                            "type": "array", 
                            "items": {"type": "array", "items": {"type": "string"}, "description": "e.g. ['A', 'B'] means A -> B"}
                        },
                        "treatment": {"type": "string"},
                        "outcome": {"type": "string"},
                        "dataset_uri": {"type": "string", "description": "URI or local path to the observational data CSV/Parquet"}
                    },
                    "required": ["nodes", "edges", "treatment", "outcome", "dataset_uri"]
                }
            }
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list:
        if name == "mcp_causal_server_estimate_effect":
            if not dowhy:
                return [{"type": "text", "text": json.dumps({"error": "DoWhy package not installed."})}]
            if not pd:
                return [{"type": "text", "text": json.dumps({"error": "pandas package not installed."})}]
            
            try:
                # 1. Reconstruct the formal DAG
                edges = arguments.get("edges", [])
                gml_graph = "digraph { "
                for edge in edges:
                    gml_graph += f'"{edge[0]}" -> "{edge[1]}"; '
                gml_graph += "}"
                
                # 2. Load observational data
                dataset_uri = arguments.get("dataset_uri")
                if dataset_uri.endswith(".parquet"):
                    df = pd.read_parquet(dataset_uri)
                else:
                    df = pd.read_csv(dataset_uri)
                    
                # 3. Instantiate CausalModel
                model = CausalModel(
                    data=df,
                    treatment=arguments.get("treatment"),
                    outcome=arguments.get("outcome"),
                    graph=gml_graph
                )
                
                # 4. Identify the estimand
                identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
                
                # 5. Estimate the causal effect
                # Using linear regression as a default robust estimator
                estimate = model.estimate_effect(
                    identified_estimand,
                    method_name="backdoor.linear_regression"
                )
                
                return [{"type": "text", "text": json.dumps({
                    "status": "success",
                    "estimand": str(identified_estimand),
                    "estimated_effect": estimate.value
                })}]
            except Exception as e:
                logger.error(f"Causal inference failed: {e}")
                return [{"type": "text", "text": json.dumps({"error": str(e)})}]
        
        raise ValueError(f"Unknown tool: {name}")

    return server

async def main():
    logger.info("Starting causal_server MCP over stdio...")
    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
