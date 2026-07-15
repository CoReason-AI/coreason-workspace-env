# Getting Started

Welcome to the CoReason Workspace Environment! This guide will help you get the platform up and running locally.

## Prerequisites

- **Python 3.14+**
- **uv** (Package Manager)
- **PostgreSQL 16+** (with `pgvector` extension)
- **Redis 5.0+**

## Installation

```bash
# Clone the repository
git clone https://github.com/CoReason-AI/coreason-workspace-env.git
cd coreason-workspace-env

# Sync dependencies
uv sync --all-extras
```

## Running the Platform

You can start the environment using the CLI:
```bash
uv run coreason dev
```
This will spin up the backend API, the MCP server, and connect to your local database.
