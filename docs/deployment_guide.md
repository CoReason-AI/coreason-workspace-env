# Deployment & Portability Guide

The CoReason Workspace Environment is designed to be highly portable and secure, specifically tailored for data-sovereign, zero-trust environments (including Standalone and Private Cloud topologies).

## 1. Containerized Services

To support asynchronous concurrency and horizontal scaling, the platform utilizes specialized Docker containers:
- **`platform_server`**: A FastAPI web server handling synchronous REST API and SSE requests.
- **`platform_worker`**: A `keda_worker` daemon pulling agent execution tasks off the Redis queue asynchronously.
- **`postgres_checkpointer`**: Handles multi-tenant safe StateGraph checkpoints and events.

## 2. Deployment Architectures

### Enterprise Kubernetes (Helm)
For large-scale, distributed deployments, the entire stack is packaged as a unified Helm chart for clusters like EKS, GKE, or AKS. The worker daemon is seamlessly autoscaled by KEDA based on Redis queue depth.

### Marketplace & Infrastructure as Code
- **OpenTofu & Terraform**: Complete IaC templates for AWS (EKS/RDS) and Azure (AKS/PostgreSQL) are located in `deploy/terraform/`.
- **AWS CloudFormation**: A 1-click serverless AWS ECS Fargate deployment template is located in `deploy/cloudformation/coreason-enterprise.yaml`.
- **GitHub Actions**: A reusable workflow is available in `.github/workflows/deploy-helm.yml` for automated CI/CD deployments.

### Air-Gapped Edge (K3s)
For internet-denied environments, the platform is available as a standalone K3s distribution, forcing all language models and tools to run locally via internal endpoints.

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
