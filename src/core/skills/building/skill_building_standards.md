# Skill Building Standards

> **Scope**: This skill is a construction guide for factory agents that **create** agentic Skills (SOPs). It defines how to structure skills, their inputs/outputs, and behavioral contracts. It does NOT contain validation checklists — those live in `validation/skill_validation_standards.md`.

---

## 1. Single Responsibility (Atomic Design)

A skill must do **one thing**. Do not bundle multiple complex operations into a single file.

- If an operation requires multiple distinct steps, break it into multiple skills
- Each skill is the equivalent of a highly encapsulated method — not a monolithic procedure
- Name skills after their single responsibility (e.g., `compress_context`, not `process_and_compress_and_validate`)

## 2. Information Hiding (Encapsulation)

The calling agent does not need to know the underlying mechanics of how a skill executes.

- **Required Inputs**: Define the exact Pydantic schema that must be passed in. If the agent lacks required data, the skill must fail immediately — not guess
- **Output Schema**: Define the strict JSON/Pydantic structure the skill returns
- Never expose internal implementation details to the caller

## 3. Idempotency & Determinism

LLMs are probabilistic. Skills must enforce determinism.

- **Idempotency**: Running the skill twice must safely yield the same result without compounding side effects
- **Refusal Predicate**: Every skill MUST define a strict refusal condition. If required external data is missing or empty, the skill must halt and return a predefined failure state (e.g., `NOT_FOUND`) rather than guessing or fabricating
- **Negative Constraints**: Explicitly define what the LLM is forbidden from doing (e.g., "DO NOT perform causal assessment here"). This prevents role bleed where a data-extraction skill accidentally starts making domain judgments

## 4. Integration Contract

Every skill MUST define an Integration Contract for framework-agnostic implementation:

- **Compute Constraints**: State whether the skill is a pure, stateless function or a stateful process
- **Side-Effect Risk**: Label the skill as `Read-Only` or `State-Mutating`. State-mutating skills require WAL or Saga compensation patterns
- **SDK Decoupling**: The algorithm must never reference specific framework SDKs. Describe logic purely mathematically or procedurally

## 5. Schema Constraints

- Output schemas must be `≤ 3` levels deep
- Parameter counts should be limited to 5-8 per level
- This maximizes deterministic LLM routing and reduces hallucination

## 6. Progressive Disclosure (JIT Loading)

Skills are loaded Just-in-Time to prevent context window dilution.

- Every skill MUST begin with a concise semantic discovery abstract at the top
- The abstract compresses the skill's purpose, inputs, outputs, and constraints into a scannable header
- The orchestrator reads only this abstract during planning and loads the full skill only when needed

## 7. Provenance (The Receipt Pattern)

If a skill fetches or processes external factual data:

- The output schema MUST include a `provenance_receipts` object — a key-value mapping of extracted claims to their source URI/citation ID
- Never allow an LLM to output factual data without structurally attaching it to a citation

## 8. Domain Source Authority

If the downstream platform defines authoritative reference sources (books, datasets, regulatory documents):

- The skill author MUST search these sources before writing algorithmic constraints
- Extract insights and embed them as native constraints in the skill — do not instruct the executing agent to "read the source" at runtime
- The intelligence must be natively embedded, not deferred

## 9. Path Portability

- All file operations must use relative paths dynamically resolved (e.g., `pathlib.Path(__file__).resolve().parent`)
- Hardcoding absolute paths or OS-specific separators is forbidden
- Skills must run seamlessly across environments
