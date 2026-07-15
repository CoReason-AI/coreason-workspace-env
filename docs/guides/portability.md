# Portability Engine

The CoReason Workspace Environment features a robust, industry-standard Portability Engine for sharing, versioning, and deploying agent projects across air-gapped environments or distributed architectures.

## Architecture

The Portability Engine operates on two primary modalities:

1. **Local Bundles (Air-Gapped)**: Extracts the workspace into a `workspace.tar.gz`, dumps the isolated Postgres tenant data into `pg_dump.sql`, and optionally exports the execution environment via `docker save`. Triggered via `export-project` and `import-project`.
2. **OCI Registry (Industry Standard)**: Packages the project alongside an [RO-Crate](https://www.researchobject.org/ro-crate/) metadata file (`ro-crate-metadata.json`) and pushes it directly to any compliant OCI registry (e.g., GitHub Container Registry, AWS ECR, Docker Hub) using `oras-py`. Triggered via `push-project` and `pull-project`.

## Granular Exports

Exporting a massive LLM agent ecosystem (including 5GB+ Docker images and heavy Postgres vector state) can be painfully slow. The Portability Engine supports **Granular Exports** to bypass heavy layers when you only want to share logic (code and YAML):

- `--skip-docker`: Bypasses the `docker save` command. The exported artifact will rely on the importing system's pre-built images.
- `--skip-state`: Bypasses the `pg_dump` command. The exported artifact will not contain any conversation history, RAG embeddings, or job statuses from the source environment.

## Async Job Tracking

Due to the size of fully-hydrated agents, exports and imports can take up to 10 minutes. The core `portability_service.py` is entirely asynchronous and decoupled from HTTP timeouts.

When you initiate a push or pull, the system:
1. Immediately creates a tracking entry in the `portability_jobs` Postgres table.
2. Hands the workload off to an `asyncio` background task.
3. Returns a `job_id`.

Clients can dynamically poll this `job_id` to get real-time status updates (`ACCEPTED`, `RUNNING`, `COMPLETED`, `FAILED`).
