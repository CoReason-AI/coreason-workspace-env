# Testing Architecture & Verification Suite

This document describes the testing philosophy, verification suite, and quality control procedures enforced within the CoReason AI Agent Building Platform (`coreason-workspace-env`).

---

## Zero-Mock, Anti-Stub Testing Philosophy

The platform operates under a strict **Zero-Mock, Anti-Stub Policy**:
- **No Hollow Stubs**: Mocks, stubs, and fakes are completely forbidden from core service execution paths (`src/core/services/`).
- **Real Integration Tests**: All catalog operations, URN resolution, sandbox provisioning, RBAC authorization, and SDK methods execute against real PostgreSQL schemas, real file system paths, and actual service layers.
- **Empirical Runtime Proof**: Code is never declared complete until verified by automated tests running under `pytest`.

---

## Test Suite Execution

### Running Full Test Suite
```bash
uv run pytest
```

### Expected Output
```text
collected 79 items

tests\test_agent_harness.py .                                            [  1%]
tests\test_agents_e2e.py ..                                              [  3%]
tests\test_api_endpoints.py ......                                       [ 11%]
tests\test_catalog_service.py ....                                       [ 16%]
tests\test_catalog_tools.py .                                            [ 17%]
tests\test_celery_tasks.py ..                                            [ 20%]
tests\test_cli.py .........                                              [ 31%]
tests\test_core.py .                                                     [ 32%]
tests\test_deepagents_compatibility.py .                                 [ 34%]
tests\test_factory_agents.py .....                                       [ 40%]
tests\test_main.py .                                                     [ 41%]
tests\test_marketplace.py ...                                            [ 45%]
tests\test_mcp.py ...........                                            [ 59%]
tests\test_parity.py .............s..                                    [ 79%]
tests\test_sandbox_service.py ..                                         [ 82%]
tests\test_sdk.py .                                                      [ 83%]
tests\test_services.py .........                                         [ 94%]
tests\test_skill_service.py ...                                          [ 98%]
tests\test_trace_service.py .                                            [100%]

======================= 78 passed, 1 skipped in 14.93s ========================
```

---

## Test Coverage Breakdown

| Test Suite File | Coverage Target | Key Features Verified |
|---|---|---|
| `test_catalog_service.py` | 100% | IANA PEN 66197 OID URN parsing, Coreason URL Authority resolution, Catalog registration, and search |
| `test_sandbox_service.py` | 100% | OpenShell Zero-Trust agent-specific boundary policy, Docker Compose sandbox, K8s pod manifest, and sandbox lifecycle |
| `test_services.py` | 100% | Quine-like project template synthesis, auto-generated README/DEPLOYMENT/DISTRIBUTION docs |
| `test_api_endpoints.py` | 100% | REST API routes for `/agents`, `/catalog`, `/sandboxes`, and RBAC authorization |
| `test_cli.py` | 100% | CLI subcommand execution across `agents`, `catalog`, `sandboxes` |
| `test_mcp.py` | 100% | FastMCP tool registration and stdio JSON-RPC tool invocation |
| `test_sdk.py` | 100% | In-process Python SDK (`CoReasonClient`) surface coverage |

---

## Continuous Integration (CI) Pipeline

All commits pushed to GitHub branches are automatically validated by CI workflows:
1. `make lint`: Ruff linting and Mypy static type checking.
2. `make format`: Auto-formatting check.
3. `uv run pytest`: 100% pass rate requirement before pull request merge.
