# Building Skills

In the CoReason Workspace Environment, an agent's capabilities are extended not through massive, hardcoded system prompts, but through modular, progressively disclosed **Skills**. 

Skills encapsulate complex workflows, domain knowledge, or specific tool integrations into strictly-typed, atomic Python `@tools`. 

## Skill Architecture

Every skill is structured as an isolated directory. By default, skills are stored in the shared library at `src/core/skills/`. To maintain the Maker-Checker pipeline, they are functionally split:
- `src/core/skills/building/`: Standards and execution tools for Maker agents.
- `src/core/skills/validation/`: Formal pass/fail checklists and AST parsers for the Checker (`agent_validator`).

### Directory Structure

A standard skill directory contains:

```text
skills/<skill_name>/
├── SKILL.md            # Required: Core instructions and metadata
├── scripts/            # Helper Python scripts for deterministic execution
├── examples/           # Reference implementations
└── references/         # Extended documentation
```

### The SKILL.md File

The `SKILL.md` file is the absolute source of truth for a skill. It contains YAML frontmatter and a Markdown body.

```markdown
---
name: generate_sql_query
description: Translates a natural language request into a strictly validated Postgres SQL query.
---

# Instructions
When invoked, you must use the `scripts/sql_generator.py` utility to ensure the query adheres to the schema...
```

- **Frontmatter**: The `name` and `description` are critical. These fields are what the YAML compiler extracts to generate the tool's signature for the agent's context window (Progressive Disclosure).
- **Body**: The Markdown body contains the specific instructions the agent will read *after* triggering the skill. Keep this under 500 lines to prevent context bloat.

## Core Mandates

When authoring a new skill, you must adhere to the following architectural constraints:

1. **Atomic Scope**: The skill must adhere to the Single Responsibility Principle. A data-retrieval primitive must never attempt semantic synthesis.
2. **Transactional Safety**: If the skill manipulates data or files, it must be idempotent or utilize Write-Ahead Logging (WAL) to prevent partial execution failures.
3. **Pydantic I/O**: All input and output contracts must be defined using strict Pydantic models (from `src.core.ontology`) with a maximum depth of 3 nested levels.
4. **Deterministic Governance**: The skill must act as a "bumper" for the stochastic LLM. The LLM invokes the primitive, but the primitive executes deterministically in Python.
