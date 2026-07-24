# End-to-End Tutorials

This guide provides step-by-step tutorials for building, sandboxing, registering, and deploying agentic applications using the CoReason AI Agent Building Factory (`coreason-workspace-env`).

---

## Tutorial 1: Building a Self-Similar Agentic Application

In this tutorial, you will use the `factory_ceo` orchestrator to synthesize a new agentic application that inherits the platform's 5-surface architecture.

### Step 1: Initialize the Application Context
Using the Python SDK:
```python
import asyncio
from src.sdk.client import CoReasonClient

async def build_agent():
    client = CoReasonClient()
    
    # 1. Search existing catalog for similar exemplars
    results = client.catalog.search(query="financial compliance")
    print("Catalog Exemplars:", results)
    
    # 2. Execute factory_ceo to synthesize the application
    response = await client.agents.execute(
        "factory_ceo",
        payload={
            "goal": "Build an enterprise financial compliance monitoring agent",
            "project_id": "fin_compliance_v1"
        }
    )
    print("Factory CEO Execution Response:", response)

asyncio.run(build_agent())
```

### Step 2: Synthesize Project Artifacts
Using `BundlerService.synthesize_project_template`:
```python
from src.core.services.bundler_service import bundler_service

project = bundler_service.synthesize_project_template(
    project_id="fin_compliance_v1",
    name="Financial Compliance Monitoring Agent",
    description="Monitors financial transactions and generates regulatory compliance reports.",
    orchestrator_yaml="agentspec_version: '26.1.2'\nname: fin_compliance_orchestrator\n",
    tools=["coreason-postgres", "coreason-fetch"],
    skills=["building/agent_building_standards"]
)

print("Synthesized URN:", project["urn"])
print("Generated Docs:", list(project["documentation"].keys()))
```

---

## Tutorial 2: Provisioning an OpenShell Zero-Trust Sandbox

In this tutorial, you will provision an isolated OpenShell sandbox environment for testing the synthesized agent.

### Step 1: Provision the Sandbox
Using the CLI:
```bash
coreason sandboxes provision --project "fin_compliance_v1" --env "test"
```

### Step 2: Inspect Generated Boundary Manifests
Inside `sandboxes/<sandbox_id>/`, observe the generated security manifests:
- `openshell.policy.json`: Process boundary and network egress whitelist.
- `docker-compose.sandbox.yaml`: Container isolation with `no-new-privileges:true`.
- `k8s-pod.yaml`: Kubernetes Pod spec with `readOnlyRootFilesystem: true`.

### Step 3: Execute Agent in Sandbox
```bash
coreason sandboxes execute --id "<sandbox_id>" --payload '{"action": "run_audit"}'
```

---

## Tutorial 3: Registering and Importing Project Modules via IANA PEN 66197 URNs

### Step 1: Register in Global Catalog
```bash
coreason catalog register --urn "urn:oid:1.3.6.1.4.1.66197:project:fin_compliance_v1" --name "Financial Compliance Monitoring Agent" --type "project"
```

### Step 2: Resolve URN
```bash
coreason catalog resolve --urn "https://urn.coreason.ai/1.3.6.1.4.1.66197/project/fin_compliance_v1"
```

### Step 3: Import Module into New Project Space
```bash
coreason catalog import --urn "urn:oid:1.3.6.1.4.1.66197:project:fin_compliance_v1" --target "new_project_space"
```

---

## Tutorial 4: Connecting the Application to Dify Enterprise Shell

1. Launch Dify locally via Docker Compose (`http://localhost:5001`).
2. Register the CoReason MCP Server tool endpoint: `http://localhost:9005/mcp`.
3. Create a Dify Chat Application and attach the imported CoReason MCP tools.
4. Interact with your agent via Dify's enterprise conversational interface!
