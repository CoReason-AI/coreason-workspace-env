# Deployment & Portability Guide

The CoReason Workspace Environment is designed to be highly portable and secure, specifically tailored for data-sovereign, zero-trust environments (including Standalone and Private Cloud topologies).

## 1. Containerized Services

To support asynchronous concurrency and horizontal scaling, the platform utilizes specialized Docker containers:
- **`platform_server`**: A monolithic FastAPI web server handling synchronous REST API requests, native `asyncio` background executions, and SSE streaming.
- **`postgres_checkpointer`**: Handles multi-tenant safe StateGraph checkpoints and events, providing the unified state backbone that enables stateless autoscaling of the server replicas.

## 2. Deployment Architectures (Cloud Only)

### Dify Enterprise Shell Integration (The Full-Code Bridge)
In production, the CoReason platform is deployed as a headless **MCP Server** and plugged into **Dify**. We strictly bypass Dify's low-code workflow builder in favor of a **Full-Code** paradigm. 
- The Python backend (running `coreason-workspace-env`) is deployed independently (e.g., via Helm or ECS).
- A production Dify instance is configured to use the CoReason MCP Server URL as an external Tool Provider.
- This creates a powerful enterprise boundary: Dify handles RBAC, horizontal UI scaling, SSO, and user chat sessions, while delegating the execution of deterministic, high-stakes LangGraph autonomous pipelines to the CoReason backend via the `run_native_deepagent` MCP tool.

For infrastructure provisioning, the platform relies on Managed Cloud Services (like AWS RDS, Elasticache, managed Vault, and S3) rather than Docker containers for stateful infrastructure.

### Marketplace & Infrastructure as Code (Terraform)
Complete IaC templates for AWS (EKS/RDS) and Azure (AKS/PostgreSQL) are located in `deploy/terraform/`. To deploy the full Cloud Only stack on AWS:

```bash
cd deploy/terraform/aws
terraform init
terraform plan -out=tfplan
terraform apply "tfplan"
```

### AWS CloudFormation (Serverless)
A 1-click serverless AWS ECS Fargate deployment template is provided. You can deploy this stack using the AWS CLI:

```bash
aws cloudformation deploy \
  --template-file deploy/cloudformation/coreason-enterprise.yaml \
  --stack-name coreason-production \
  --capabilities CAPABILITY_IAM
```

### Enterprise Kubernetes (Helm)
For large-scale, distributed deployments, the entire stack is packaged as a unified Helm chart for clusters like EKS, GKE, or AKS. The `platform_server` replicas are seamlessly autoscaled based on HTTP load (e.g. via HPA), ensuring responsive synchronous endpoints and horizontally distributed `asyncio` task processing.

To install the release via Helm:
```bash
helm repo add coreason https://charts.coreason.ai
helm install coreason-workspace coreason/coreason-workspace -f values.yaml
```

A reusable GitHub Actions workflow is also available in `.github/workflows/deploy-helm.yml` for automated CI/CD deployments.

### Air-Gapped Edge (K3s)
For internet-denied environments, the platform is available as a standalone K3s distribution, forcing all language models and tools to run locally via internal endpoints.

### Single-Node Standalone (Windows & Linux)
To run the full stack on a single bare-metal node or VM with native OS service parity (Systemd / Windows Services), refer to the [Standalone Services Guide](services.md).

## 3. Immutable Agent Sandboxes

A critical security mandate is **Deterministic Dependencies**. The platform utilizes the **NemoClaw for Deep Agents** blueprint.
- **Governed Sandboxes**: Agents operate strictly within isolated Kubernetes pod sandboxes managed by the NVIDIA OpenShell Gateway.
- **No Dynamic Installs**: Dynamic `pip install` commands at runtime are forbidden. All dependencies must be strictly locked and baked into the image during CI/CD.

## 4. Portability Engine

The Portability Engine allows sharing, versioning, and deploying agent projects across environments. Due to massive file sizes, the core `portability_service.py` is fully asynchronous and tracks progress via `portability_jobs`.

### Modalities
1. **Local Bundles (Air-Gapped)**: Extracts the workspace into `workspace.tar.gz`, dumps tenant data into `pg_dump.sql`, and exports Docker images. Triggered via `export-project` and `import-project`.
2. **OCI Registry (Industry Standard)**: Packages the project alongside an RO-Crate metadata file and pushes it directly to compliant OCI registries (GHCR, AWS ECR, Docker Hub) using `oras-py`. Triggered via `push-project` and `pull-project`.

### Granular Exports
To bypass heavy layers when only sharing logic:
- `--skip-docker`: Bypasses the `docker save` command.
- `--skip-state`: Bypasses the `pg_dump` command, excluding conversation history and RAG embeddings.

## 5. Security & IAM Configuration

The following environment variables govern the Zero-Trust and Supply Chain Security pipelines at runtime:

- `VAULT_ADDR`: The address of the HashiCorp Vault server.
- `VAULT_NAMESPACE`: The Vault namespace for secrets isolation.
- `VAULT_DEV_ROOT_TOKEN_ID`: The root token for Vault authentication.
- `LLM_API_KEY` / `LLM_BASE_URL`: Governs external LLM routing securely.
- `WORM_S3_ACCESS_KEY` / `WORM_S3_SECRET_KEY`: Credentials for the Write-Once-Read-Many (WORM) storage.
