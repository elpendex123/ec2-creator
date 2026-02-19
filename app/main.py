from fastapi import FastAPI
from app.routers import instances
from app.services.db import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EC2 Provisioner API",
    description="FastAPI REST API for provisioning and managing AWS EC2 instances",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    db._ensure_db_exists()
    logger.info("Database initialized")


@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes liveness probes."""
    return {"status": "ok"}


# Include routers
app.include_router(instances.router)
