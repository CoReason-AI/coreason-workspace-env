# Command Line Interface (CLI)

The CoReason Workspace Environment mandates strict **Multi-Surface Parity**. The Command Line Interface is a first-class interaction surface, providing complete parity with the REST API and the Model Context Protocol (MCP).

All CLI operations are natively integrated into the shared `src.core.services` layer. Anything achievable through the web dashboard or API is equally achievable in an air-gapped terminal.

## The NemoClaw CLI Installer & DeepAgents TUI (`dcode`)

The environment utilizes the advanced **DeepAgents Code TUI** (`dcode`) as its primary terminal-based user interface, deployed and governed by the **NemoClaw CLI installer**. 

This powerful Text User Interface is invoked directly via the `dcode` shell alias. As part of the NemoClaw for Deep Agents blueprint, `dcode` runs the agent explicitly inside an NVIDIA OpenShell secure sandbox, powered by Nemotron 3 Ultra.

Rather than relying on proprietary, one-off synchronous HTTP requests, `dcode` operates as a native **MCP Client**. It automatically discovers the platform's headless MCP server and interacts with the internal LangGraph state machine via standard tools and prompt resources.

### Capabilities
- **Rich Interactive UI**: Built on `textual`, providing an IDE-like terminal experience.
- **Agent Orchestration**: Execute complex agent workflows (Maker-Checker validation pipelines) natively from the terminal.
- **Accordion Task Tracking**: Agent steps, tracker task lists, and summary updates are displayed via expandable accordions, shielding you from raw log spew.
- **Real-Time State Streaming**: Connects to the platform's RFC 6902 JSON Patch streams to observe deterministic workflow routing without polling.

### Typer Implementation
The CLI natively wraps the shared `orchestration_service` using `Typer`. For example, invoking the `coreason build` command seamlessly initiates the full Maker-Checker workflow, guaranteeing exact feature parity with the `/export` HTTP endpoints.

For heavy async operations, such as `coreason push-project`, `coreason pull-project`, `coreason export-project`, and `coreason import-project`, the CLI abstracts the background polling loop entirely. It utilizes the synchronous Python SDK and wraps the execution in a gorgeous `rich` animated spinner, giving you immediate terminal feedback while the system extracts Docker images in the background. You can also pass `--skip-state` and `--skip-docker` directly to these commands.

Additional operational commands include `coreason agents list`, `coreason agents get`, and `coreason mcp list-servers`, which all provide rich JSON output compliant with the API schema.

## Connecting the CLI

To launch the CLI and interface with your CoReason Workspace Environment:

```bash
# Ensure the MCP server definition (.mcp.json) is present in the workspace
# Export the API token so the CLI can authenticate with the secured platform
export COREASON_API_TOKEN="coreason-dev-token"
uv run dcode
```

Since the environment operates as a headless MCP server, `dcode` abstracts away the topology complexity. Upstream operations are handled deterministically within the platform and streamed directly to your terminal.
