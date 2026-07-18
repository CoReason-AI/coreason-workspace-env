# Six Thinking Hats Evaluation

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Preventing Groupthink in high-stakes strategic or regulatory decisions.
> **Origin**: Inspired by the `six_thinking_hats_evaluation_tool.md` from the Fractal Study.

When building an Orchestrator or a decision-making agent tasked with evaluating a critical strategic dilemma (e.g., "Should we acquire this biotech?" or "Is this safety signal a risk?"), you must prevent premature consensus by forcing adversarial, multi-perspective evaluation.

### The Six Hats Prompting Structure
Inject the following explicit rules into the agent's `<Workflow>`:

1. **Cognitive Isolation**: "Do not attempt to synthesize an answer immediately. You must first explicitly generate 6 distinct evaluation blocks, one for each cognitive mode."
2. **The 6 Nodes**:
   - `<White_Hat>`: Pure facts, data, and available evidence. No interpretation.
   - `<Red_Hat>`: Emotion, intuition, and stakeholder perception (e.g., patient fear, market reaction).
   - `<Black_Hat>`: Devil's Advocate. Strictly focus on risks, methodological flaws, and worst-case scenarios.
   - `<Yellow_Hat>`: Optimism. Strictly focus on the best-case benefits and value generation.
   - `<Green_Hat>`: Creativity. Propose lateral alternatives (e.g., repurposing the drug, alternative trial designs).
   - `<Blue_Hat>`: The Control node. Synthesize the competing 5 nodes into a mathematically or logically weighted final recommendation.
3. **Bleed Prevention**: "Ensure that the Black Hat analysis does not prematurely try to mitigate the risks—it must only surface them. Mitigation is reserved for the Blue Hat."
