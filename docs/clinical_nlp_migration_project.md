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

---

### Learnings on Observability (Langfuse)
As an Agent Improvement System, full "Glass Box" traceability is required to debug and refine agent execution. We leverage **Langfuse** for tracing.

**Why we need it:**
- **Execution Graph Transparency:** The `factory_ceo` and `agent_pm` orchestrate complex Maker-Checker loops using LangGraph. If a sub-agent (like `agent_validator`) fails repeatedly, Langfuse provides exact insight into the LLM prompts, tool invocations, and responses that led to the failure.
- **Context Propagation:** When dynamically injecting Langfuse callbacks into a running graph, it is critical to pass the `RunnableConfig` object down from the orchestrator to the sub-agents. Creating new, orphaned `CallbackHandler` instances inside nested LLM calls breaks the trace hierarchy and causes `KeyError` crashes, as the parent graph state is lost.
- **Harmless SDK Warnings:** Due to the massive telemetry payloads our orchestrators send to the local Langfuse container, the Python SDK may occasionally throw background warnings in the terminal (e.g. `Unexpected error occurred. Please check your request and contact support`). These are non-fatal asynchronous synchronization warnings and can be safely ignored.

### Learnings on Context Engineering & Tool Calling
- **Autonomous vs Static Context Injection:** We originally relied on a Python wrapper (`orchestration_service.py`) to blindly unzip and read the legacy codebase, statically injecting it into the orchestrator's prompt. 
- **DeepAgent ReAct Loop:** We realized this violates the DeepAgent philosophy. We refactored `factory_ceo` to act as a true State Machine. It now utilizes a LangChain `@tool` (`extract_and_read_context`) inside a LangGraph `ToolNode`. The LLM actively decides to invoke the tool when given a path, reads the codebase, and explicitly determines when its context is saturated.

### Learnings on Formal Output Validation (Maker-Checker)
During our migration, the `AgentValidator` successfully caught several subtle generative errors produced by the `YamlCompiler` during its compilation of the legacy code:
1. **YAML String Syntax Errors:** The compiler injected a stray closing brace (`'}'}`) at the end of a stringified JSON schema, invalidating the YAML structure.
2. **Dependency Naming:** The compiler used arbitrary naming (`NER Agent`) in the `dependencies` array instead of the strict `snake_case` matching the agent's ID (`ner_agent`).
3. **JSON Schema Keyword Collisions:** The compiler generated an object schema containing a property literally named `type`. This conflicts with the JSON Schema `type` reserved keyword.
4. **Cross-Platform Paths:** The compiler generated Windows-style backslashes (`\`) for file paths.
**Remediation:** We immediately fed these learnings back into the platform by explicitly updating the `yaml_compiler`'s system prompt to forbid these anti-patterns, improving the reliability of the entire platform.

---

## 3. Execution Trigger

With the infrastructure healthy, we trigger the orchestrator via the CLI:

```bash
uv run coreason build "we want you to transform this legacy NLP pipeline that involve sentence restructuring, NER, NEN with UMLS tagging CUI into an enterprise grade encapsulated mcp deployable agentic solution. give me a multi agent topology to work it. we want an escalcalating cascade that starts with smaller models (non transformer or transformer) and goes up the chain as the confidence goes down. let us try to do true to original implementation for now." --input-path "./clinical_concept_normalization_legacy" --output-dir "./projects/clinical_nlp_mcp"
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
- [ ] Run the `build` command.
- [ ] Review the generated multi-agent topology in `./projects/clinical_nlp_mcp`.
- [ ] Remediate any `agent_validator` failures via our Agent Improvement tools (Langfuse trace retrieval, Postgres state inspection).
