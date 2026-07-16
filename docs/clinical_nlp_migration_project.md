# Clinical NLP Migration Project

This document serves as our shared running pad to track the migration of the legacy Clinical NLP codebase into an enterprise-grade, MCP-deployable agentic solution using the CoReason Workspace environment. 

By documenting our setup, configuration, and execution logs here, we ensure our work is fully reproducible.

---

## 1. Goal & Intent

Our objective is to trigger the `factory_ceo` orchestrator with the following intent:
> "we want you to transform this legacy NLP pipeline that involve sentence restructuring, NER, NEN with UMLS tagging CUI into an enterprise grade encapsulated mcp deployable agentic solution. give me a multi agent topology to work it. we want an escalcalating cascade that starts with smaller models (non transformer or transformer) and goes up the chain as the confidence goes down. let us try to do true to original implementation for now."

**Input Context**: `./clinical_concept_normalization_legacy`
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
Configure the platform to connect to your preferred Model-as-a-Service (MaaS) provider for the primary reasoning engine.

```env
# MaaS API Key
MAAS_API_KEY=sk-...

# LLM Configuration
LLM_MODEL_NAME=openai/gpt-4o-mini
LLM_API_KEY=${MAAS_API_KEY}
LLM_TEMPERATURE=0.0
LLM_BASE_URL=https://api.openai.com/v1
```

### Launching Infrastructure
Once `.env` is configured, start the background infrastructure (Postgres checkpointer, Langfuse, Vault, Redis, and workers):
```bash
docker compose up -d
```

### Learnings on Docker Infrastructure & Standalone Mode

**Langfuse v3 Database Migration Issue**
Langfuse recently introduced a v3 architecture that strictly requires Clickhouse. The default `docker-compose.yaml` in this repository pulled `langfuse/langfuse:latest`, which automatically fetched v3. Without a Clickhouse instance, this resulted in an infinite crash loop.

Additionally, Langfuse uses Prisma ORM, which throws fatal `P3005` errors if it attempts to migrate into a non-empty database schema (e.g. sharing `langgraph_state` with the agents).
**Remediation:** 
1. We carved out a dedicated, empty `langfuse` database inside the Postgres container so Prisma could initialize without colliding with LangGraph's state tables.
2. We added `clickhouse/clickhouse-server:23.12-alpine` natively into the `docker-compose.yaml` as the `clickhouse` service, complete with data persistence.
3. We configured `langfuse/langfuse:latest` with the appropriate `CLICKHOUSE_URL`, `CLICKHOUSE_MIGRATION_URL`, `CLICKHOUSE_USER`, and `CLICKHOUSE_PASSWORD` connection strings to fully adopt the v3 architecture and its performant OLAP backend.

**ClickHouse Configuration Learnings:**
- **Port Conflict:** ClickHouse uses TCP port `9000` by default. Since the `docker-compose.standalone.yaml` overrides use MinIO (which also binds to `9000`), we successfully avoided host collision by mapping ClickHouse to `9002:9000` on the host, while retaining `9000` for the internal `CLICKHOUSE_MIGRATION_URL`.
- **Clustering:** Langfuse v3 expects ClickHouse to run in a Zookeeper cluster by default. Since we run a single-node standalone ClickHouse container, we had to explicitly set `CLICKHOUSE_CLUSTER_ENABLED: "false"` in Langfuse to prevent `code: 139` table creation crashes.
- **Strict Schema Validation:** Langfuse v3 utilizes strict Zod schema validation during startup. It threw fatal errors for missing S3 credentials (e.g., `LANGFUSE_S3_EVENT_UPLOAD_BUCKET`) even when telemetry was disabled. We injected dummy values into the `.yaml` to satisfy the validator and allow the container to start.

**Sovereign / Air-gapped Mode (`docker-compose.standalone.yaml`)**
We determined that running the `docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml up -d --build` command should **only** be executed in two specific scenarios:
1. **Developing Platform Core**: Modifying the FastAPI backend or worker code and needing to rebuild the images from source.
2. **Sovereign Execution**: Overriding the `.env` settings to force the platform to use local, air-gapped models via **Ollama** (e.g., `llama3`) and local S3 storage via **MinIO**.

**Warning:** Using the standalone override while doing complex agent building (like our current task) will swap out flagship models like `gpt-4o` for smaller local models that lack the instruction-following capacity to adhere to strict validation rules, leading to immediate validation loop failures.

---

### Learnings on Observability (Langfuse)
As an Agent Improvement System, full "Glass Box" traceability is required to debug and refine agent execution. We leverage **Langfuse** for tracing.

**Why we need it:**
- **Execution Graph Transparency:** The `factory_ceo` and `agent_pm` orchestrate complex Maker-Checker loops using LangGraph. If a sub-agent (like `agent_validator`) fails repeatedly, Langfuse provides exact insight into the LLM prompts, tool invocations, and responses that led to the failure.
- **Context Propagation:** When dynamically injecting Langfuse callbacks into a running graph, it is critical to pass the `RunnableConfig` object down from the orchestrator to the sub-agents. Creating new, orphaned `CallbackHandler` instances inside nested LLM calls breaks the trace hierarchy and causes `KeyError` crashes, as the parent graph state is lost.
- **Harmless SDK Warnings:** Due to the massive telemetry payloads our orchestrators send to the local Langfuse container, the Python SDK may occasionally throw background warnings in the terminal (e.g. `Unexpected error occurred. Please check your request and contact support`). These are non-fatal asynchronous synchronization warnings and can be safely ignored.

### Learnings on Context Engineering & Epistemic Isolation
- **Epistemic Firewall (CEO Strict Isolation):** We learned that giving the `factory_ceo` orchestrator direct tools to read files bloated its context window. To enforce the Epistemic Firewall, we removed the `extract_and_read_context` tool from the CEO entirely. Instead, the CEO routes raw input paths to the `librarian_pm`, which extracts the codebase, generates an architectural summary using a specialized `ContextCompressorAgent`, and returns only the summarized string back to the CEO. The CEO now strictly evaluates the "typed text" of the user's intent.
- **DeepAgent State Machine & Interrogation Loops:** The CEO now operates as a true State Machine using LangGraph's checkpointer. If the user's intent lacks strict constraints (not SATURATED), the CEO pauses the LangGraph execution at an `interrogate_user` node.
- **CLI Conversational Interaction:** We updated the `coreason build` CLI script into a `while True:` loop that captures the CEO's clarifying questions via `typer.prompt()`. Because LangGraph automatically persists thread state using Postgres, appending the user's typed response to the CLI seamlessly resumes the CEO's evaluation exactly where it left off, creating a native multi-turn loop!

### Learnings on DeepAgent Runtime Configuration
- **Hardcoded Standalone Placeholders vs Vault:** While auditing `deepagent_runtime.py` (the blueprint runtime deployed alongside generated agent projects), we discovered that the LLM instantiation was hardcoding the API key to `"standalone-key-placeholder"` and the model to `"nvidia/nemotron-3-nano-30b-a3b:free"`. 
  - **The Reason:** The runtime is designed for an enterprise, air-gapped target cluster where secrets are injected dynamically via HashiCorp Vault at runtime, entirely bypassing `.env` files for security compliance.
  - **The Fix:** For local, standalone testing and development, hardcoding these values prevented the runtime from utilizing the `.env` MaaS keys (e.g., GPT-4o keys). We refactored `deepagent_runtime.py` to seamlessly fallback to the SSOT `settings` (e.g. `settings.LLM_API_KEY`) if the `project_manifest` doesn't provide them, allowing both secure production Vault usage and smooth local LLM testing.

### Learnings on Formal Output Validation (Maker-Checker)
During our migration, the `AgentValidator` successfully caught several subtle generative errors produced by the `YamlCompiler` during its compilation of the legacy code:
1. **YAML String Syntax Errors:** The compiler injected a stray closing brace (`'}'}`) at the end of a stringified JSON schema, invalidating the YAML structure.
2. **Dependency Naming:** The compiler used arbitrary naming (`NER Agent`) in the `dependencies` array instead of the strict `snake_case` matching the agent's ID (`ner_agent`).
3. **JSON Schema Keyword Collisions:** The compiler generated an object schema containing a property literally named `type`. This conflicts with the JSON Schema `type` reserved keyword.
4. **Cross-Platform Paths:** The compiler generated Windows-style backslashes (`\`) for file paths.
**Remediation:** We immediately fed these learnings back into the platform by explicitly updating the `yaml_compiler`'s system prompt to forbid these anti-patterns, improving the reliability of the entire platform.

### Learnings on Model Reasoning Capacity
We initially used `gpt-4o-mini` for the factory agents. However, it repeatedly failed the Maker-Checker validation loop because it lacked the instruction-following capacity to adhere to strict YAML formatting rules (e.g. not indenting top-level keys). We attempted to switch to `nvidia/llama-3.1-nemotron-70b-instruct` on OpenRouter, but encountered a `404 No endpoints found` availability error. 

To resolve this, we updated our `.env` configuration to use the flagship `openai/gpt-4o` model. Using a significantly more capable reasoning model improved the platform's ability to output correctly formatted schemas without hallucinating structure.

### Learnings on Checker Loop Termination
Even with GPT-4o successfully formatting the output, we discovered a logical bug in the `AgentValidator`'s prompt. The validator flagged the missing `security` field as a `WARN`, correctly noting it does not block disk writes. However, it incorrectly evaluated the "Overall Status" as `FAIL`. This triggered an infinite retry loop in `agent_pm` because the PM graphs interprets any `FAIL` overall status as a mandate to remediate.
**Remediation:** We updated the `agent_validator`'s system prompt to explicitly enforce: `CRITICAL: If an artifact only has PASS and WARN results, you MUST set the overall status to PASS.`

---

## 3. Execution Trigger

With the infrastructure healthy, we trigger the orchestrator via the CLI:

```bash
uv run coreason build "we want you to transform this legacy NLP pipeline that involve sentence restructuring, NER, NEN with UMLS tagging CUI into an enterprise grade encapsulated mcp deployable agentic solution. give me a multi agent topology to work it. we want an escalcalating cascade that starts with smaller models (non transformer or transformer) and goes up the chain as the confidence goes down. let us try to do true to original implementation for now." --input-path "./clinical_concept_normalization_legacy/clinical-definition-synthesizer" --output-dir "./projects/clinical_nlp_mcp"
```

---

## 4. Scratchpad & Execution Log

*(This space is reserved for pasting CLI outputs, agent traces, and our running notes as the factory agents build the solution)*

### Agent Observations:
- **[2026-07-15]**: Triggered the CLI command. The `factory_ceo` successfully invoked its context ingestion tool, extracted the zips, and delegated to the `agent_pm`. 
- **[2026-07-15]**: The Maker-Checker loop executed. `YamlCompiler` generated the pipelines but failed validation due to JSON schema `type` property conflicts and strict dependency naming requirements.
- **[2026-07-15]**: Updated the `yaml_compiler` system prompt with strict rules for generating valid schemas and dependency references. Build restarted.

---

## 5. Outstanding Tasks
- [x] Run the `build` command.
- [ ] Review the generated multi-agent topology in `./projects/clinical_nlp_mcp`.
- [ ] Remediate any `agent_validator` failures via our Agent Improvement tools (Langfuse trace retrieval, Postgres state inspection).
