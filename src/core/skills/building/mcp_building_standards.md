# MCP Building Standards

> **Scope**: This skill is a construction guide for factory agents that **create** MCP server specifications. It defines how to structure MCP servers, tools, and integration contracts. It does NOT contain validation checklists — those live in `validation/mcp_validation_standards.md`.

---

## 1. The Zero-Trust Boundary

An MCP Server is an **epistemic firewall** between reasoning agents and the external world (databases, APIs, enterprise systems).

- Agents MUST NOT write arbitrary SQL, invoke `requests.get()`, or directly call external APIs
- All external interactions flow exclusively through standardized MCP Tools
- **Resource Mapping**: If the server provides access to static documents or datasets, map them as MCP Resources with predictable URI templates
- **Tool Encapsulation**: If the server provides active capabilities (searching, mutating state), define each as a distinct MCP Tool with strict input/output schemas

## 2. Integration Contract

Every MCP server specification MUST define an Integration Contract to ensure framework-agnostic mountability:

- **Transport Protocol**: State whether the server runs locally via `stdio` or remotely via `sse`. This dictates how the orchestrator configures the connection
- **Authentication**: List all required environment variables or secrets. Never hardcode credentials — reference environment variables or a secrets manager
- **Rate Limits & Concurrency**: Explicitly define the rate limits and concurrency constraints of the underlying system so orchestrators can configure circuit breakers

## 3. The Provenance / Receipt Pattern

If an MCP server fetches external factual data, it MUST NOT return raw text strings.

- **Mandatory Provenance**: Output of data-retrieval tools MUST be structured to include citation identifiers or source URIs
- Every retrieved claim must be traceable to its origin
- This enables downstream agents to cryptographically prove the origin of their claims
- **Output structure must include**: the data payload AND a `provenance_receipts` mapping (claim → source URI/citation ID)

## 4. Tool Design Rules

- Each MCP Tool must have a clear, single responsibility
- Input schemas must use strict Pydantic models — no arbitrary dicts or untyped parameters
- Output schemas must be `≤ 3` levels deep with 5-8 parameters maximum
- Error responses must be structured and actionable, not raw exception strings
- Tools that mutate state must enforce caller-supplied `idempotency_keys`
