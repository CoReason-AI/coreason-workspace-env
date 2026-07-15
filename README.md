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
[![LangGraph](https://img.shields.io/badge/LangGraph-Native-black?style=flat)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)]()
[![MCP](https://img.shields.io/badge/MCP-Server-8A2BE2?style=flat)]()

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
1. **[DeepAgent Pattern](docs/architecture/deepagent_pattern.md)**: YAML-driven progressive disclosure.
2. **[Maker-Checker Pipeline](docs/architecture/maker_checker.md)**: Strict separation of duties.
3. **[Epistemic Firewall](docs/architecture/epistemic_firewall.md)**: Zero-trust knowledge retrieval and strict provenance tracking.
4. **[Interaction Surfaces](docs/surfaces/mcp_server.md)**: Complete parity across MCP, CLI, REST API, WebSocket, and SDK.

## Maintenance & Rules

For guidelines on how AI agents must modify this repository, see `AGENTS.md`.