# CoReason Workspace Environment

[![Python](https://img.shields.io/badge/Python-3.14-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License: Prosperity 3.0](https://img.shields.io/badge/License-Prosperity_3.0-blue.svg)](https://prosperitylicense.com/versions/3.0.0)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-94%25-brightgreen.svg)]()
[![Powered By: AI](https://img.shields.io/badge/Powered%20By-CoReason%20AI-FF4500.svg)](https://coreason.ai)
<br>
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/CoReason-AI/coreason-workspace-env?label=OpenSSF)](https://scorecard.dev/viewer/?uri=github.com/CoReason-AI/coreason-workspace-env)
[![TruffleHog](https://img.shields.io/github/actions/workflow/status/CoReason-AI/coreason-workspace-env/trufflehog.yml?branch=main&label=TruffleHog)](https://github.com/CoReason-AI/coreason-workspace-env/actions/workflows/trufflehog.yml)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

**Tech Stack:**
[![DeepAgents](https://img.shields.io/badge/deepagents-%E2%9C%A8-blue)](https://github.com/langchain-ai/deepagents)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)]()
[![MCP](https://img.shields.io/badge/MCP-Server-8A2BE2?style=flat)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Checkpointer-4169E1?style=flat&logo=postgresql&logoColor=white)]()
[![ClickHouse](https://img.shields.io/badge/ClickHouse-OLAP-FFCC01?style=flat&logo=clickhouse&logoColor=black)]()
[![Redis](https://img.shields.io/badge/Redis-PubSub-DC382D?style=flat&logo=redis&logoColor=white)]()
[![Vault](https://img.shields.io/badge/HashiCorp_Vault-Secrets-000000?style=flat&logo=hashicorp-vault&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?style=flat&logo=docker&logoColor=white)]()

**The Headless Agent Development Platform.**

`coreason-workspace-env` is a LangGraph DeepAgent-based, multi-user, project-oriented, opinionated platform where humans and AI agents collaborate to design, build, test, and deploy opinionated agentic platforms — each seamlessly deployable as MCP servers (Model Context Protocol).

## Documentation

Full documentation is built using MkDocs. 

**To view the documentation locally:**
```bash
uv sync --all-extras
uv run mkdocs serve
```

### Key Pillars
1. **[DeepAgent Pattern](docs/core_architecture.md#deepagent-pattern--declarative-manifests)**: YAML-driven progressive disclosure and structured eventing (Accordion UX).
2. **[Builder-Validator-Approver](docs/vignette_mangalore_news.md#4-delegation-and-the-builder-validator-approver-workflow)**: Strict separation of duties and deterministic artifact validation.
3. **[Epistemic Firewall](docs/core_architecture.md#the-epistemic-firewall-zero-trust-rag)**: Zero-trust knowledge retrieval and strict provenance tracking.
4. **[Interaction Surfaces](docs/interaction_surfaces.md)**: Complete parity across MCP, REST API, CLI, WebSocket (JSON Patch Streaming), and SDK.

## Maintenance & Rules

For guidelines on how AI agents must modify this repository, see `AGENTS.md`.

## Observability

We strictly use **Langfuse** for local LLM tracing and agent performance evaluations via the Harbor container stack.

### 1. Spin up the Telemetry Infrastructure
Start the containerized stack:
* **Linux/macOS:**
  ```bash
  harbor up langfuse
  ```
* **Windows (via WSL2):** Run the PowerShell bridge script:
  ```powershell
  .\scripts\start_observability.ps1
  ```

> [!TIP]
> If the `harbor.langfuse-clickhouse` container fails to start with a permission error, run the following command to fix host directory ownership:
> ```bash
> sudo chown -R 101:101 ~/.harbor/services/langfuse/data/clickhouse-data
> sudo chown -R 101:101 ~/.harbor/services/langfuse/data/clickhouse-logs
> ```

### 2. Configure Credentials
1. Open the local dashboard: **http://localhost:33881**
2. Click **Sign up** to create a local account.
3. Go to **Settings > API Keys** and click **Generate API Keys**.
4. Add these keys to your `.env` file:
   ```env
   LANGFUSE_SECRET_KEY="sk-lf-..."
   LANGFUSE_PUBLIC_KEY="pk-lf-..."
   LANGFUSE_HOST="http://localhost:33881"
   ```

### 3. Run and Verify Tracing
Install the required packages in your virtual environment and execute the orchestrator:
```bash
# Install Langfuse SDK in the project virtual environment
uv pip install langfuse

# Run an agent to generate traces
uv run coreason agents execute "factory_ceo" "Write a clinical trial platform agent manifest"
```
Refresh your Langfuse UI to view the live execution tree, latency metrics, and LLM input/outputs.