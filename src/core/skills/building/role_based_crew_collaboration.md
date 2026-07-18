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
`"You are part of a crew. If you need X, delegate to the Lead_Copywriter. If you need Y, delegate to the Senior_Researcher."`
