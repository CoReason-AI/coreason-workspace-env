import logging
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.api.router import api_router
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI platform.
    Initializes Redis connections for the Pub/Sub backplane and Celery/KEDA queues.
    """
    logger.info("Initializing CoReason Workspace Environment (Headless Core)...")
    logger.info("-> Mock: Initializing Redis Pub/Sub Backplane")
    logger.info("-> Mock: Connecting to Postgres LangGraph Checkpointer...")
    # In production: pool = await asyncpg.create_pool(DSN)
    yield
    logger.info("Shutting down CoReason Workspace Environment...")
    logger.info("-> Mock: Closing Postgres Checkpointer pool.")

# Initialize FastAPI App
app = FastAPI(
    title="CoReason Multi-User Agent Workspace",
    description="Scalable, Async, Multi-Tenant LangGraph API.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# --- MULTI-USER ASYNC EXECUTION DEMO ---

class AgentRunRequest(BaseModel):
    user_id: str
    tenant_id: str
    crude_context: str

def execute_agent_background_task(job_id: str, run_req: AgentRunRequest):
    """
    Simulates a long-running LangGraph compilation task executing in the background.
    Demonstrates Tenant Sandbox Isolation and Thread ID routing.
    """
    # 1. Isolate the Workspace
    tenant_sandbox_path = f"/tmp/coreason_sandboxes/{run_req.tenant_id}/"
    logger.info(f"[JOB {job_id}] Securing Tenant Sandbox at: {tenant_sandbox_path}")
    
    # 2. Configure LangGraph Postgres Thread Isolation
    # We pass the user_id as the thread_id so Postgres handles the locking.
    thread_id = f"thread_{run_req.user_id}"
    logger.info(f"[JOB {job_id}] Locking Postgres Checkpointer State for thread: {thread_id}")
    
    # 3. Simulate Long-Running Execution
    logger.info(f"[JOB {job_id}] DeepAgent Supervisor orchestrating workload...")
    time.sleep(3) # Simulate heavy LLM reasoning
    
    logger.info(f"[JOB {job_id}] Workflow Complete. Wrote artifacts to {tenant_sandbox_path}")

@app.post("/api/v2/agents/project_initiation/async_run")
async def run_project_initiation_async(req: AgentRunRequest, background_tasks: BackgroundTasks):
    """
    Non-blocking endpoint for multi-user interaction.
    Returns a Job ID immediately while the agent orchestrates in the background.
    """
    if not req.user_id or not req.tenant_id:
        raise HTTPException(status_code=400, detail="Multi-user endpoints require user_id and tenant_id for isolation.")
        
    job_id = str(uuid.uuid4())
    
    # Hand the execution off to the Task Queue (FastAPI BackgroundTasks or Celery)
    background_tasks.add_task(execute_agent_background_task, job_id, req)
    
    return {
        "status": "Accepted",
        "job_id": job_id,
        "message": "The DeepAgent supervisor has begun execution in the background.",
        "poll_url": f"/api/v2/jobs/{job_id}"
    }

@app.get("/health")
async def health_check():
    """
    KEDA and Kubernetes native health check endpoint.
    """
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
