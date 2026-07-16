# Clinical NLP Migration Project

This document outlines the project for using the headless CLI to spin up a new multi-agent platform designed to modernize the legacy Clinical NLP codebase. We will use the Nemotron 70B model via OpenRouter as our upstream reasoning engine.

## Prerequisites

- **Python 3.14+** and **uv** installed.
- **PostgreSQL 16+** and **Redis 5.0+** running.

## Step 1: Bypassing the Local GPU

By default, the standalone platform relies on Ollama to run a local model on your GPU. In this tutorial, we will shift to the cloud using the **Nemotron 70B** model provided by OpenRouter.

1. Open your `.env` file at the root of the repository.
2. Update your LLM configurations to point to OpenRouter:

```env
# APIs
OPENROUTER_API_KEY=sk-or-v1-...

# LLM Configuration
LLM_MODEL_NAME=nvidia/llama-3.1-nemotron-70b-instruct-free
LLM_API_KEY=${OPENROUTER_API_KEY}
LLM_TEMPERATURE=0.0
LLM_BASE_URL=https://openrouter.ai/api/v1
```

This configuration ensures all Maker-Checker agents will securely authenticate against OpenRouter instead of trying to hit a local GPU inference container.

## Step 2: Launching the Factory Engine

Before we can use the CLI, we need the background worker (which processes the generated tasks) and the core API running. You can run these using standard `docker compose` without the standalone override (which would attempt to download and start Ollama):

```bash
docker compose up -d
```

## Step 3: Context Ingestion & Intent

The CLI is a direct interface to the `factory_ceo` orchestrator. In addition to a high-level intent, you can pass unstructured context files to the platform. This context can be an unzipped directory or a `.zip` archive containing anything—Markdown docs, PowerPoint presentations, PDF specifications, Python scripts, legacy agents, or entire MCP servers.

Run the following command in your terminal to pass your context archive and your high-level intent:

```bash
uv run coreason build "we want you to transform this legacy NLP pipeline that involve sentence restructuring, NER, NEN with UMLS tagging CUI into an enterprise grade encapsulated mcp deployable agentic solution. give me a multi agent topology to work it. we want an escalcalating cascade that starts with smaller models (non transformer or transformer) and goes up the chain as the confidence goes down. let us try to do true to original implementation for now." --input-path "./clinical_concept_normalization_legacy.zip" --output-dir "./projects/clinical_nlp_mcp"
```

### Context Saturation & Interrogation

The `factory_ceo` operates as a strict state machine. It will ingest your provided context files and evaluate if it has enough information to proceed. If your context files and intent are underspecified (e.g., missing security requirements or target platform details), the CEO will not simply guess. It will initiate an interrogation loop—"grilling" you with targeted, clarifying questions through the CLI. 

You must answer these questions until the CEO determines its internal context threshold is fully saturated. Only then will it stop communicating and delegate the payload to the specialized PM agents.

## Step 4: Observation & Remediation

Once context is saturated, the orchestrator delegates the payload to the specialized deterministic sub-agents:
- The `agent_pm` orchestrating task breakdown.
- The `prompt_engineer` generating specialized system prompts.
- The `yaml_compiler` strictly mapping DeepAgent YAML definitions.
- The `agent_validator` formally evaluating the generated code.

You can observe these agents iterating and communicating directly in your CLI output. If the `agent_validator` flags a violation, you will see a remediation loop dynamically redirecting the execution trace back to the offending Maker agent.

## Step 5: Exporting the Bundle

Once all validation checks have passed, the platform dynamically synthesizes a `pyproject.toml` and packages your new agent platform into an immutable ZIP bundle.

You can then push it directly to your OCI registry:
```bash
uv run coreason push_project <project_id> ghcr.io/my-org/trial-agent:v1.0.0
```

Your cloud-powered, CLI-driven multi-agent platform is now ready for deployment!
