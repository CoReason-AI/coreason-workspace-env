import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    # TODO: Initialize Redis Pub/Sub Backplane
    # TODO: Initialize LangGraph checkpointer connection (Postgres)
    yield
    logger.info("Shutting down CoReason Workspace Environment...")
    # TODO: Cleanup connections

# Initialize FastAPI App
app = FastAPI(
    title="CoReason Agent Workspace Platform",
    description="Decoupled, CISO-Grade Sovereign Opinionated Agent Dev and Test Platform.",
    version="1.0.0",
    lifespan=lifespan
)

# CISO-Grade CORS Middleware (To be configured for the Edge Proxy Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """
    KEDA and Kubernetes native health check endpoint.
    """
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
