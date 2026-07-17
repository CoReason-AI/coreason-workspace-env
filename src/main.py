import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.api.router import api_router
from src.core.config import settings
from src.core.db import get_db_pool, close_db_pool
from src.core.services import health_service, project_service, portability_service
from src.core.security.auth import get_current_user, UserIdentity


# Load environment variables
load_dotenv()

# Configure logging and OpenTelemetry
try:
    from src.core.telemetry import setup_telemetry
    setup_telemetry()
    logger = logging.getLogger(__name__)
    logger.info("OpenTelemetry and structlog telemetry initialized successfully.")
except Exception as e:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to initialize OpenTelemetry/structlog: {e}. Falling back to standard logging.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI platform.
    Initializes database tables, Redis connections, and Pub/Sub backplane.
    """
    logger.info("Initializing CoReason Workspace Environment (Headless Core)...")

    # Bootstrap database schema
    try:
        await get_db_pool()
        logger.info("-> Global connection pool initialized.")
        await project_service.initialize()
        logger.info("-> Postgres: Projects table initialized.")
        await portability_service.initialize()
        logger.info("-> Postgres: Portability jobs table initialized.")
    except Exception as e:
        logger.warning(f"-> Postgres initialization skipped: {e}")

    yield
    logger.info("Shutting down CoReason Workspace Environment...")
    await close_db_pool()
    logger.info("-> Global connection pool closed.")

# Initialize FastAPI App
app = FastAPI(
    title="CoReason Multi-User Agent Workspace",
    description="Scalable, Async, Multi-Tenant LangGraph API.",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.streaming import events, ws_endpoints

app.include_router(api_router, prefix="/api/v1")
app.include_router(events.router)
app.include_router(ws_endpoints.router)


# --- Multi-User Async Execution ---

class AgentRunRequest(BaseModel):
    user_id: str
    tenant_id: str
    crude_context: str


@app.post("/api/v2/agents/{agent_name}/async_run")
async def run_agent_async(
    agent_name: str, 
    req: AgentRunRequest, 
    background_tasks: BackgroundTasks,
    user: UserIdentity = Depends(get_current_user)
):
    """
    Non-blocking endpoint for multi-user agent execution.
    Returns a Job ID immediately while the agent orchestrates in the background.
    """
    from src.core.services import agent_service

    if not req.user_id or not req.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Multi-user endpoints require user_id and tenant_id for isolation.",
        )

    if user.user_id != req.user_id and "Supervisor" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="Authenticated user does not match the requested execution user_id or lack supervisory privileges.",
        )

    result = await agent_service.execute_agent(
        agent_name=agent_name,
        payload={"crude_context": req.crude_context},
        user_id=req.user_id,
        tenant_id=req.tenant_id,
    )
    return result



@app.get("/health")
async def health_check():
    """
    Health check endpoint — checks Postgres, Redis connectivity.
    Used by KEDA, Kubernetes, and monitoring tools.
    """
    return await health_service.check()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
