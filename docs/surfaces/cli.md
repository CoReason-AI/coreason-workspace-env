# Command Line Interface (CLI)

The CLI provides headless, scriptable access to the platform, ideal for CI/CD pipelines and air-gapped environments.

## Usage

```bash
uv run coreason [command]
```

## Key Commands

*   `init`: Scaffold a new project.
*   `dev`: Run `langgraph dev` against a bundled project.
*   `deploy`: Deploy the platform to LangGraph Cloud or a local Kubernetes cluster.

## Design Rules

The CLI outputs structured JSON by default (parseable by scripts and upstream agents) with an optional `--pretty` flag for human-readable formatting.
