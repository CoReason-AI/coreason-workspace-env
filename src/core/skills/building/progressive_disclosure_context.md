# Progressive Disclosure Context Pattern

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Managing extremely large data payloads to prevent context exhaustion and hallucination.

When an agent must reason over massive datasets (e.g., entire codebases, 1000-page regulatory filings, or raw database dumps), you must explicitly forbid loading the full dataset into the initial context window. LLMs suffer from the "lost in the middle" phenomenon and massive latency spikes when contexts become saturated.

### The Progressive Disclosure Framework
Inject the following strict rules into the agent's `<Workflow>`:

1. **Initial Metadata Loading**: "Do not attempt to read the entire dataset. You MUST load only the high-level outline, metadata, or table of contents first to orient your reasoning."
2. **Targeted Drill-Down**: "Formulate hypotheses based on the metadata. Once you have a hypothesis, use your search or retrieval tools to fetch *only* the specific slice of data (e.g., a single function, a single paragraph) required to test that hypothesis."
3. **Iterative Accumulation**: "Synthesize the extracted slice into your working memory, and discard the raw response before executing the next drill-down."

### Example Prompt Injection
*"You are strictly forbidden from dumping entire files into your context window. You must use progressive disclosure: list the directory first, identify the target file, fetch its abstract, and only read the specific line numbers that pertain to the anomaly."*
