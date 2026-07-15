# Python SDK

For programmatic access and tight integration, the CoReason Workspace Environment exposes a native Python SDK. 

This SDK acts as the fifth and final interaction surface, providing identical capabilities to the REST API, CLI, and MCP server, but engineered for native in-process execution.

## In-Process Embedding

The Python SDK is designed for scenarios where the headless platform needs to be directly embedded into an upstream Python application (such as an existing Airflow pipeline, a custom Django backend, or a Jupyter notebook).

```python
import coreason

# Initialize the embedded platform client with your API token
client = coreason.Client(token="coreason-dev-token")

# Execute an agent workflow deterministically
receipt = client.agents.execute(
    agent_id="data_extractor",
    payload={"source_file": "report.pdf"}
)

print(receipt.outputs)
```

## Async Native

The entire SDK is built asynchronously using `asyncio`, mirroring the async nature of the underlying FastAPI and LangGraph architecture. This allows for high-throughput concurrency when orchestrating multiple agentic workflows simultaneously.

For streaming interactions (like tracking the live LangGraph state of a long-running agent), the SDK yields asynchronous iterators, providing identical telemetry to the WebSocket surface.

```python
import asyncio
import coreason

async def monitor_agent():
    client = coreason.AsyncClient(token="coreason-dev-token")
    
    # Subscribe to the real-time state sync stream
    async for state in client.streaming.watch_state(session_id="uuid7-1234"):
        print(f"Current Node: {state.node_name}")
        print(f"Pending Edges: {state.next}")

asyncio.run(monitor_agent())
```

## Schema Parity

Just like the REST API, the Python SDK relies entirely on the `coreason-manifest` library for its type hints and return schemas. This means IDEs will provide perfect auto-completion for all agent outputs and Epistemic Firewall bounds, leveraging the strictly-typed Pydantic geometry.
