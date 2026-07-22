import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.router import api_router
from src.core.config import settings

# Configure logging and Telemetry
from src.core.telemetry import setup_telemetry
setup_telemetry()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI App
app = FastAPI(
    title="CoReason Multi-User Agent Workspace",
    description="Scalable, Async, Multi-Tenant LangGraph API.",
    version="2.1.0",
)

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
