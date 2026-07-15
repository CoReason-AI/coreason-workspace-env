# Deploying the Platform

The CoReason Workspace Environment is designed to be highly portable and secure. Because it frequently processes sensitive corporate data or proprietary logic, the deployment architecture is strictly tailored for sovereign, zero-trust environments.

## Containerized Services

To support true asynchronous concurrency and horizontal scaling, the platform utilizes specialized Docker containers defined in the `docker-compose.yaml`:
- **`platform_server`**: A FastAPI web server handling synchronous REST API and SSE requests.
- **`platform_worker`**: A `keda_worker` daemon pulling agent execution tasks off the Redis queue asynchronously.
- **`postgres_checkpointer`**: Handles multi-tenant safe StateGraph checkpoints and events.

## Deployment Architectures

The platform can be deployed in two primary configurations:

### 1. Enterprise Kubernetes (Helm)
For large-scale, distributed deployments, the entire orchestrator, Postgres Checkpointer, and execution nodes are packaged as a unified Helm chart. This allows for seamless deployment into existing enterprise Kubernetes clusters (e.g., EKS, GKE, AKS). The worker daemon is deployed via `worker-deployment.yaml` and seamlessly autoscaled by KEDA based on the queue depth monitored on the queue specified by `REDIS_QUEUE_NAME`.

#### Infrastructure as Code (OpenTofu & Terraform)
To support 1-click enterprise deployments, the `deploy/terraform/` directory contains complete Infrastructure as Code (IaC) templates for both AWS (EKS/RDS) and Azure (AKS/PostgreSQL). 

These templates use standard HCL syntax and are **100% compatible with both Terraform and OpenTofu**. To provision the platform using OpenTofu, simply use the `tofu` CLI in place of `terraform`:
```bash
cd deploy/terraform/aws
tofu init
tofu apply
```

### 2. Air-Gapped Edge (K3s)
For highly secure, internet-denied environments (such as on-premise defense or pharmaceutical R&D labs), the platform is available as a standalone K3s distribution. The platform natively functions completely air-gapped; all language models must run locally or via an internal VPC endpoint, and all tools must rely on internal data.

## Immutable Agent Sandboxes & The NemoClaw Blueprint

A critical security mandate for production deployment is **Deterministic Dependencies** and zero-trust execution. The platform utilizes the **NemoClaw for Deep Agents** blueprint as its reference architecture for securing agent operations.

When an agent is deployed, it is packaged as a standalone Docker image defined by its `project.yaml` manifest. 
- **NemoClaw Governed Sandboxes**: Agents operate strictly within isolated, ephemeral Kubernetes pod sandboxes managed by the **NVIDIA OpenShell Gateway** (part of the NemoClaw stack). This ensures that autonomous operations on sensitive codebases proceed without risk of data exfiltration.
- **No Dynamic Installs**: Dynamic `pip install` commands at runtime are mathematically forbidden. All dependencies must be strictly locked and baked into the image during the CI/CD pipeline. This guarantees that an agent deployed today will execute identically three years from now, and prevents supply-chain attacks in air-gapped environments.

## The Model Context Protocol

Once deployed, the easiest way to interact with the cluster is via the Model Context Protocol (MCP). The entire platform exposes itself as a headless MCP server. 

Simply configure your enterprise IDE or upstream orchestrator to point to the cluster's MCP endpoint, and the complex LangGraph topologies will instantly become available as localized, highly capable tools.
