# Zero Waste Architecture

## Core Philosophy
The "Zero Waste" architecture mandates that we do not maintain custom code for capabilities that are natively provided by stable, mature Open Source ecosystem projects. We prefer a **thin factory approach**.

## Dify Integration
- **Dify Replaces Custom Services**: Dify natively handles Orchestration, Multi-Tenant Projects, Authentication, Tracing, and Portability. 
- **Code Deletion**: We have actively deleted `project_service.py`, `orchestration_service.py`, `db.py`, and the entire `security` module. 
- **Local Embedded Dify**: Dify is embedded directly into our local `docker-compose.yaml` (API, Worker, Postgres, Redis) to provide a complete standalone sandbox.

## Zero Mock Testing
- Mocks (`unittest.mock`) are strictly forbidden when verifying API boundaries.
- All testing must hit local Ephemeral Testcontainers.
- Tests that require full Dify API boundaries are stripped to avoid heavy multi-container bloat during CI/CD.
