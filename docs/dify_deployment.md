# Deploying CoReason MCP to Dify Enterprise API Gateway

This guide outlines how to deploy the CoReason MCP Agent Bundle and configure Dify to act as the Enterprise API Gateway, bypassing Dify's visual builder in favor of a full-code, air-gapped architecture.

## 1. Build the Encrypted MCP Bundle

During CI/CD, run the bundler CLI command to encrypt all agent YAML manifests:

```bash
uv run coreason mcp bundle --source src/agents --output dist/coreason_mcp_bundle.enc
```
This produces a monolithic AES-256 encrypted bundle using the native `bundler_service.py` component.

## 2. Deploy the Karta Container (K3s)

Deploy the `coreason-mcp-bundle` Docker image to your K3s cluster. 
Ensure the Pod has the correct Cloud IAM / Workload Identity annotations to access the Cloud KMS. At runtime, the `AgentService` will lazily decrypt the bundle in-memory upon the first MCP request if the `MCP_BUNDLE_PATH` environment variable is set.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coreason-mcp
spec:
  template:
    metadata:
      annotations:
        # Example for AWS EKS IAM Roles for Service Accounts
        eks.amazonaws.com/role-arn: arn:aws:iam::111122223333:role/mcp-kms-decryption-role
    spec:
      containers:
      - name: mcp-server
        image: coreason/mcp-bundle:latest
        env:
        - name: MCP_TRANSPORT
          value: "sse"
        - name: CLOUD_KMS_PROVIDER
          value: "aws"
        - name: KMS_SECRET_NAME
          value: "/coreason/mcp/bundle_key"
        ports:
        - containerPort: 8000
```

## 3. Configure Dify API Gateway

We rely on Dify solely for API key management, load balancing, and Server-Sent Events (SSE) streaming.

1. **Start Dify (Self-Hosted/Docker Compose):**
   Follow Dify's local deployment guide. Make sure the Dify container is on the same internal virtual network as the K3s Ingress or Open Shell Sandbox.
2. **Add the MCP Tool in Dify:**
   Navigate to `Tools -> Custom -> Add Tool`.
   Select **MCP** and choose **SSE Transport**.
   Point the URL to your CoReason MCP service: `http://coreason-mcp.internal.svc.cluster.local:8000/sse`
3. **Expose as API:**
   In Dify, create a basic application (Chat/Agent) that uses this single MCP tool. 
   Go to **API Access** and generate an API key. 
   You can now bypass the Dify UI completely. Have your Streamlit app connect directly to the Dify API using this key.

## 4. Telemetry Verification

Traces are automatically routed to the Langfuse backend via the OpenTelemetry Collector Sidecar deployed in the Open Shell Sandbox. You do not need to configure Langfuse in Dify, as the deepagents are emitting traces natively via OTEL.
