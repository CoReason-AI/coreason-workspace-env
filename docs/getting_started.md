# Getting Started

Welcome to the CoReason Workspace Environment! This guide will help you get the platform up and running locally.

## Prerequisites

- **Python 3.14+**
- **uv** (Package Manager)
- **PostgreSQL 16+** (with `pgvector` extension)

## Configuration

The platform adheres to strict enterprise security practices. All LLM configurations are centralized and managed via environment variables using `pydantic-settings`.

Before running the platform, configure your environment:
```bash
cp .env.example .env
```
Open `.env` and set your `LLM_API_KEY`, `LLM_MODEL_NAME`, and `LLM_BASE_URL`. This allows you to securely swap between cloud providers or local vLLM deployments without touching the source code.
Additionally, ensure you set `API_SECRET_TOKEN` to secure the platform endpoints.

> [!TIP]
> **CLI Local Overrides:** When testing the CLI locally against a running Docker Compose standalone stack, you may need to override environment variables inline so the CLI targets your local mapped ports and models instead of external defaults. For example:
> ```powershell
> $env:LLM_BASE_URL="http://127.0.0.1:11434/v1"; $env:LLM_MODEL_NAME="llama3"; $env:POSTGRES_PORT="5434"; uv run coreason agents execute "yaml_compiler" "Build a system..."
> ```

## Installation

```bash
# Clone the repository
git clone https://github.com/CoReason-AI/coreason-workspace-env.git
cd coreason-workspace-env

# Sync dependencies
uv sync --all-extras
```

## Running the Platform

The CoReason platform relies on a distributed multi-tenant architecture utilizing PostgreSQL, Native Async Background Tasks, and a high-performance Web Server. 

> [!NOTE]
> **Tenant Isolation:** LangGraph state checkpointers do not use the `public` schema. The runtime engine dynamically manages schema isolation (`project_{project_id}`) per tenant, ensuring zero data leakage and safe backups via `pg_dump`. 

### Starting the Services (Topologies)

The CoReason platform supports three deployment topologies depending on your needs:

1. **Local Only**: A fully localized Docker Compose stack including local LLM inference (Ollama) and local S3-compatible storage (MinIO).
2. **Hybrid**: A Docker Compose stack for core infrastructure (Postgres, Vault) but relies on Cloud API endpoints for LLMs (OpenAI, OpenRouter) and S3 via `.env`.
3. **Cloud Only**: Production-ready deployments to Enterprise Kubernetes (EKS/AKS) using Terraform, OpenTofu, or Helm.

> [!NOTE]
> For the exact CLI commands and detailed steps to run the **Local Only** or **Hybrid** topologies, please refer to the [Developer Guide](developer_guide.md#3-local-development-topologies). 
> For **Cloud Only** deployment steps, see the [Deployment Guide](deployment_guide.md#2-deployment-architectures).

### Interacting with the Platform

Because the platform is headless, you have two primary ways to interact:

**1. Interactive Dify UI (Recommended)**
Connect a local or cloud instance of **Dify** to your running MCP Server (`http://localhost:9005/mcp`). Dify will handle all conversational chat memory, rendering the interactive UI and streaming updates while the CoReason workspace executes the deep agent hierarchies in the background.

**2. Direct API via Swagger UI**
You can explore and test the raw execution endpoints directly from your browser by navigating to the Swagger UI:

`http://localhost:9005/docs`

**Authentication**: 
To execute endpoints via the Swagger UI or via cURL, you must authenticate. Click the green "Authorize" button and input your `API_SECRET_TOKEN` as a Bearer token. If you did not explicitly set this in your `.env` file, use the default local development token: `coreason-dev-token`.

### Tracing and Observability (Harbor)

To capture and view OpenTelemetry and Langfuse traces locally without using public SaaS, we use **Harbor** (a local container manager). 

### 1. Start the Observability Stack

- **Windows**: Run `.\scripts\start_observability.ps1` in PowerShell.
- **Linux/Mac**: Run `harbor up langfuse`

This will spin up the local Langfuse/Harbor container stack to capture traces. The platform is pre-configured to route all traces to this local instance.

### 2. View Traces

### Standalone Troubleshooting & Testing

If you encounter issues during a local standalone build:
- **Corrupted Builds (`no such file or directory` errors for `uvicorn`)**: Ensure the `.dockerignore` file exists in the root of the repository and includes `.venv`. Without it, local Windows/macOS `.venv` directories will overwrite the container's internal Linux `.venv` during the multi-stage build `COPY . .` command.
- **Testing inside Airgapped Containers**: The production `Dockerfile` is strictly "Airgap Ready", meaning build and development tools (like `uv` and `pytest`) are explicitly excluded from the final image stage. If you need to verify environment connectivity inside a running container, use the pure-Python standard library test script rather than `pytest`:
  ```bash
  docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml exec platform_server python tests/test_standalone_env.py
  ```

## Executing Exported Artifacts

When you build agents through the platform, it exports an installable ZIP archive containing the generated YAML manifests and a dynamically synthesized `pyproject.toml`. 

To run a generated agent:
1. Extract the ZIP archive.
2. Navigate into the extracted directory.
3. Run `uv run coreason dev` (or `uv run` depending on the generated nodes).
