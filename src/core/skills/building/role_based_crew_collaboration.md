# Role-Based Crew Collaboration

> **Taxonomy Bucket**: persona/
> **Scope**: Building flat, peer-to-peer agent networks (CrewAI topology).

When the user requests an agent network designed for collaborative brainstorming, creative generation, or open-ended research, Builders must construct a Role-Based Crew topology rather than a rigid Orchestrator-Worker tree.

### The Crew Topology
1. **Roles are Mutually Exclusive**: Define specific, non-overlapping roles (e.g., `Senior_Market_Researcher`, `Lead_Copywriter`, `Quality_Assurance_Editor`).
2. **Peer-to-Peer Delegation**: Agents in a crew do not have a single boss. They have a shared context space and are explicitly prompted to delegate tasks to their peers when they reach the edge of their domain expertise.
3. **Task vs Goal**: The crew operates on a shared macro-goal, but individual agents self-assign micro-tasks based on their declared role.

**Prompting Rule**:
Each agent's system prompt must include an explicit manifest of the other agents in the crew and their capabilities:
15: `"You are part of a crew. If you need X, delegate to the Lead_Copywriter. If you need Y, delegate to the Senior_Researcher."`
16: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a requested workflow requires strict determinism, auditable sequential execution, or rigid hierarchical control, halt and refuse to use the Crew topology. Use the SOP or Plan-and-Execute topology instead.
- **Negative Constraints**: Agents in a peer-to-peer crew must never assume they have unilateral authority over the final macro-goal without consulting their specialized peers.
