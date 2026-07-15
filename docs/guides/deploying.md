# Deploying the Platform

The CoReason Workspace Environment can be deployed to the cloud or run entirely air-gapped at the edge.

## LangGraph Cloud

To deploy to LangGraph Cloud, use the CLI:
```bash
uv run coreason deploy
```

## Kubernetes / K3s (Air-Gapped)

For enterprise edge deployments, the platform is packaged as a unified Helm chart. 

*   Agents operate strictly within isolated, ephemeral Kubernetes pod sandboxes (OpenShell Gateway). 
*   Dynamic `pip install` is forbidden in production to guarantee deterministic, air-gap ready dependencies.
