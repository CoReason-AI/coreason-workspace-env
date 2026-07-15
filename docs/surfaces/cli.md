# Command Line Interface (CLI)

The CoReason Workspace Environment mandates strict **Multi-Surface Parity**. The Command Line Interface is a first-class interaction surface, providing complete parity with the REST API. 

All CLI operations are thin transport adapters over the shared `src.core.services` layer. Anything achievable through the web dashboard or API is equally achievable in an air-gapped terminal via the CLI.

## Core Commands

The CLI is invoked via the `coreason` shell alias (or `python -m src.cli.main`). 

It provides command groups mirroring the platform's core architecture:
- `health`: Check platform health (Postgres, Redis) and version information.
- `projects`: Create, list, delete, and export agent projects for air-gap transfer.
- `agents`: Execute agent workflows, check job status, and retrieve agent definitions.
- `mcp`: List connected MCP servers and manually execute MCP tools.
- `docs`: Generate documentation scaffolds.
- `state`: Manage and visualize state synchronization.

## Output Formatting

By default, the CLI outputs perfectly structured **JSON**, making it natively parseable by upstream CI/CD pipelines, bash scripts, and orchestrating agents. 

For human readability in the terminal, you can append the `--pretty` flag to any command to format the output.

```bash
uv run coreason projects list --pretty
```

## Real-Time State Debugging

Because the platform uses the LangGraph Postgres Checkpointer to save the state of every single node execution, you don't have to restart a 10-step agent workflow just because step 8 failed.

The CLI provides a dedicated time-travel debugger that connects directly to the platform's WebSocket streaming backend:

```bash
uv run coreason state watch --session-id <session_id>
```

### The `rewind` Command
While watching the live JSON stream of LangGraph state updates, you can type `rewind <checkpoint_uuid7>` at the prompt. 

The CLI uses the `prompt_toolkit` library to gracefully handle asynchronous output collisions—meaning the live JSON stream will print *above* your prompt without garbling your keystrokes. When you issue a rewind command, the platform will instantly rollback the agent's state to that exact checkpoint in the Postgres database, allowing you to edit your code and resume execution perfectly from the point of failure.
