# How-To Recipes & Technical Guides

This collection of recipes provides practical instructions for operating and configuring the CoReason AI Agent Building Platform across all 5 interaction surfaces.

---

## Recipe 1: Executing Agents Across All 5 Interaction Surfaces

### 1. REST API (FastAPI)
```bash
curl -X POST "http://localhost:8000/agents/factory_ceo/execute" \
     -H "Content-Type: application/json" \
     -d '{"payload": {"goal": "Build news synthesis pipeline"}}'
```

### 2. CLI (`typer`)
```bash
coreason agents execute --name "factory_ceo" --payload '{"goal": "Build news synthesis pipeline"}'
```

### 3. MCP Server (`fastmcp`)
Call tool `execute_agent`:
```json
{
  "agent_name": "factory_ceo",
  "payload": {"goal": "Build news synthesis pipeline"}
}
```

### 4. WebSockets / SSE
Connect to `ws://localhost:8000/ws/agents/factory_ceo/stream` to receive real-time execution tokens and step updates.

### 5. Python SDK
```python
from src.sdk.client import CoReasonClient

client = CoReasonClient()
res = client.agents.execute("factory_ceo", payload={"goal": "Build news synthesis pipeline"})
```

---

## Recipe 2: Configuring Agent-Specific OpenShell Zero-Trust Policies

To declare custom network egress rules and tool permissions for an agent, add a `zero_trust_policy` section to `src/agents/<agent_name>/agent.yaml`:

```yaml
name: "financial_auditor"
type: "worker"
description: "Audits financial records"

zero_trust_policy:
  strict_mode: true
  allowed_egress_domains:
    - "api.sec.gov"
    - "urn.coreason.ai"
  read_only_paths:
    - "/etc"
    - "/usr"
    - "/lib"
  allowed_tools:
    - "coreason-postgres"
    - "coreason-fetch"
  allow_subprocess: false
  allow_raw_sockets: false
```

When provisioned, `SandboxService` generates `openshell.policy.json` enforcing these exact parameters!

---

## Recipe 3: Searching and Resolving Catalog URNs

### OID URN Format:
`urn:oid:1.3.6.1.4.1.66197:project:my_project`

### Coreason URL Format:
`https://urn.coreason.ai/1.3.6.1.4.1.66197/project/my_project`

### Searching via SDK:
```python
client = CoReasonClient()
results = client.catalog.search(query="compliance", tag="synthesized")
```

### Resolving via SDK:
```python
entry = client.catalog.resolve("urn:oid:1.3.6.1.4.1.66197:project:my_project")
print("Resolved Entry:", entry)
```

---

## Recipe 4: Configuring OpenTelemetry & Langfuse Local Observability

Run the local telemetry stack:
```bash
docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml up -d langfuse otel-collector
```

Set environment variables in `.env`:
```env
LANGFUSE_PUBLIC_KEY=pk-lf-123456
LANGFUSE_SECRET_KEY=sk-lf-654321
LANGFUSE_HOST=http://localhost:3000
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

Traces and execution spans will automatically stream into Langfuse and OpenTelemetry collectors.
