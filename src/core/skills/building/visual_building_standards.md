# Visual Building Standards

> **Scope**: This skill is a construction guide for factory agents that **create** architecture diagrams and workflow visualizations. It defines node/edge symbology and diagram structure. It does NOT contain validation checklists — those live in `validation/visual_validation_standards.md`.

---

## Core Principles

1. **Deterministic Representation**: Visuals must represent actual state transitions and topological structures — not vague conversational flows
2. **Standardized Protocols**: Every node interaction must be annotated with the underlying communication protocol
3. **Roles over Individuals**: Nodes represent discrete agentic roles (e.g., `Supervisor: Agent PM`), not generalized "AI components"
4. **Clean Taxonomy**: Use standard terms like *Constraint Propagation*, *Sequential Thinking*, *Delegation*, *Escalation*

## Node Symbology

The shape of the node dictates its function:

| Shape | Syntax | Usage | Example |
|---|---|---|---|
| **Trigger / Entry Point** | `[]` | Initiating event or final output state | `A["Trigger: User Request Received"]` |
| **Agent** | `()` | Deployed agent fulfilling a role. Prefix with structural domain | `B("Supervisor: Factory CEO")` |
| **Database / System** | `[()]` | External system or data store integration | `D[("mcp: postgres_checkpointer")]` |
| **Decision Gate** | `{}` | Conditional logic or validation gate | `C{"Is Context Saturated?"}` |

## Edge Symbology

The style of the edge conveys the nature of the transition:

| Style | Syntax | Usage | Annotation |
|---|---|---|---|
| **Sequential / Standard** | `-->` | Standard task delegation, data handoffs, sequential logic | `(mcp: sequentialthinking)` |
| **Executive Mandate** | `==>` | Top-down directives, overrides, strict compliance constraints | `(mcp: sequentialthinking)` |
| **Debate / Escalation** | `-.->` | Cross-functional consensus, deadlock resolution, adversarial synthesis | `(mcp: multi-agent-debate)` |

## Diagram Structure

### Shared Goal Narrative
Every workflow visualization must be preceded by a `## The Multi-Agentic Shared Goal` section that:
1. Explains how the discrete agents coordinate
2. Defines the pipeline type (e.g., *Agent Compilation Pipeline*, *Validation Pipeline*)
3. States the shared objective

### Diagram Header
All Mermaid graphs must use the dark theme for visual consistency:
```mermaid
graph TD
    %%{init: {'theme': 'dark'}}%%
```

### Edge Annotations
Every edge connecting two agents MUST define:
- The **action** being performed (e.g., "Delegate Compilation", "Validate Schema")
- The **protocol** in parentheses (e.g., `(mcp: sequentialthinking)`)
