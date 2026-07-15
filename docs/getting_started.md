# Getting Started

Welcome to the CoReason Workspace Environment! This guide will help you get the platform up and running locally.

## Prerequisites

- **Python 3.14+**
- **uv** (Package Manager)
- **PostgreSQL 16+** (with `pgvector` extension)
- **Redis 5.0+**

## Configuration

The platform adheres to strict enterprise security practices. All LLM configurations are centralized and managed via environment variables using `pydantic-settings`.

Before running the platform, configure your environment:
```bash
cp .env.example .env
```
Open `.env` and set your `LLM_API_KEY`, `LLM_MODEL_NAME`, and `LLM_BASE_URL`. This allows you to securely swap between cloud providers or local vLLM deployments without touching the source code.
Additionally, ensure you set `API_SECRET_TOKEN` to secure the platform endpoints, and `REDIS_QUEUE_NAME` (which defaults to `tasks`) if you are customizing the KEDA worker deployment.

## Installation

```bash
# Clone the repository
git clone https://github.com/CoReason-AI/coreason-workspace-env.git
cd coreason-workspace-env

# Sync dependencies
uv sync --all-extras
```

## Running the Platform

The CoReason platform relies on a distributed multi-tenant architecture utilizing PostgreSQL, Redis, and a background task daemon. The easiest way to spin this up locally is via Docker Compose:

```bash
docker-compose up -d --build
```

This will automatically spin up the `platform_server`, `postgres_checkpointer`, `redis_queue`, and `platform_worker` components. The REST API and SSE streams will be available, and the MCP server will dynamically query the Postgres database for state tracking.

> [!TIP]
> **Going to Production?**
> If you are deploying to an enterprise environment (AWS, Azure), check out our [Deploying Guide](guides/deploying.md) for 1-click Terraform, OpenTofu, and CloudFormation templates.

## Executing Exported Artifacts

When you build agents through the platform, it exports an installable ZIP archive containing the generated YAML manifests and a dynamically synthesized `pyproject.toml`. 

To run a generated agent:
1. Extract the ZIP archive.
2. Navigate into the extracted directory.
3. Run `uv run coreason dev` (or `uv run` depending on the generated nodes).
