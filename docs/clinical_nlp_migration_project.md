# Clinical NLP Migration Project

This document serves as our shared running pad to track the migration of the legacy Clinical NLP codebase into an enterprise-grade, MCP-deployable agentic solution using the CoReason Workspace environment. 

By documenting our setup, configuration, and execution logs here, we ensure our work is fully reproducible.

---

## 1. Goal & Intent

Our objective is to trigger the `factory_ceo` orchestrator with the following intent:
> "we want you to transform this legacy NLP pipeline that involve sentence restructuring, NER, NEN with UMLS tagging CUI into an enterprise grade encapsulated mcp deployable agentic solution. give me a multi agent topology to work it. we want an escalcalating cascade that starts with smaller models (non transformer or transformer) and goes up the chain as the confidence goes down. let us try to do true to original implementation for now."

**Input Context**: `./clinical_concept_normalization_legacy.zip`
**Target Output**: `./projects/clinical_nlp_mcp`

---

## 2. Setup & Configuration

To ensure reproducibility across different environments, the platform relies on strict `.env` configuration for its Single Source of Truth (SSOT). 

### Configuring the `.env` file
1. Copy the default `.env.example` to `.env` at the root of the repository:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and ensure the following critical blocks are present.

**Observability & Vault**:
```env
# Vault
VAULT_ADDR=http://vault:8200
VAULT_NAMESPACE=admin
VAULT_DEV_ROOT_TOKEN_ID=root

# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-1234567890
LANGFUSE_SECRET_KEY=sk-lf-1234567890
LANGFUSE_HOST=http://localhost:3001
```

**LLM Routing**:
We are overriding the local GPU to use a cloud-hosted reasoning engine (e.g., Nemotron 70B via OpenRouter).
```env
# APIs
OPENROUTER_API_KEY=sk-or-v1-...

# LLM Configuration
LLM_MODEL_NAME=nvidia/llama-3.1-nemotron-70b-instruct-free
LLM_API_KEY=${OPENROUTER_API_KEY}
LLM_TEMPERATURE=0.0
LLM_BASE_URL=https://openrouter.ai/api/v1
```

### Launching Infrastructure
Once `.env` is configured, start the background infrastructure (Postgres checkpointer, Langfuse, Vault, Redis, and workers):
```bash
docker compose up -d
```

---

## 3. Execution Trigger

With the infrastructure healthy, we trigger the orchestrator via the CLI:

```bash
uv run coreason build "we want you to transform this legacy NLP pipeline that involve sentence restructuring, NER, NEN with UMLS tagging CUI into an enterprise grade encapsulated mcp deployable agentic solution. give me a multi agent topology to work it. we want an escalcalating cascade that starts with smaller models (non transformer or transformer) and goes up the chain as the confidence goes down. let us try to do true to original implementation for now." --input-path "./clinical_concept_normalization_legacy.zip" --output-dir "./projects/clinical_nlp_mcp"
```

---

## 4. Scratchpad & Execution Log

*(This space is reserved for pasting CLI outputs, agent traces, and our running notes as the factory agents build the solution)*

### Agent Observations:
- **[TBD]**: Run the CLI command to populate this log.
- **[TBD]**: Await the `factory_ceo` context interrogation (if any).

---

## 5. Outstanding Tasks
- [ ] Run the `build` command.
- [ ] Review the generated multi-agent topology in `./projects/clinical_nlp_mcp`.
- [ ] Remediate any `agent_validator` failures via our Agent Improvement tools (Langfuse trace retrieval, Postgres state inspection).
