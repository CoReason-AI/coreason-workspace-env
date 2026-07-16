# SOP Simulation Hierarchy

> **Scope**: Building strict sequential corporate pipelines (MetaGPT / ChatDev topology).

When the user requests a software engineering or highly regulated manufacturing pipeline, Builders must construct an SOP Simulation hierarchy.

### The SOP Topology
Unlike a collaborative crew, an SOP topology strictly mirrors corporate waterfall methodologies. Agents do not collaborate freely; they pass serialized artifacts downstream.

1. **The Waterfall Pipeline**: `CEO` -> `Product_Manager` -> `System_Architect` -> `Senior_Engineer` -> `QA_Tester`.
2. **Artifact Passing**: 
   - The `CEO` receives the user intent and outputs a `BusinessRequirement.json`.
   - The `Product_Manager` reads `BusinessRequirement.json` and outputs `PRD.md`.
   - The `System_Architect` reads `PRD.md` and outputs `SystemDesign.yaml`.
3. **Zero Collaboration**: Agents are blind to the steps that occurred before their immediate upstream dependency. They rely entirely on the structured artifact passed to them.

**Prompting Rule**:
The system prompt for an SOP agent must declare its exact input dependency and its exact output schema. It must never attempt to communicate with downstream agents; it simply serializes its artifact and halts.
