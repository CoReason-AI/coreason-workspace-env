# Building Skills

Skills are the atomic units of execution in the DeepAgent pattern. They encapsulate complex logic, API calls, or database queries into deterministic Python `@tools`.

## Rules for Skills

1.  **Atomic Scope:** A skill should do one thing perfectly (Single Responsibility Principle).
2.  **Transactional Safety:** Use Idempotency keys and write-ahead logging (WAL) for destructive actions.
3.  **Strict I/O:** Define inputs and outputs using Pydantic models. Keep nesting ≤ 3 levels deep.
4.  **No Interrogation:** Skills must never ask the user questions. They must fail fast if required parameters are missing.

## Location

Building standards for Maker agents are located in `src/core/skills/building/`.
