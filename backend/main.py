"""
Main FastAPI application for KVM/QEMU/OVN Cluster Management
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import hosts, vms, networks, cluster
from database import engine, init_db
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.api.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager"""
    logger.info("Starting KVM Cluster Management API")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Cleanup
    logger.info("Shutting down KVM Cluster Management API")


# Create FastAPI application
app = FastAPI(
    title="KVM/QEMU/OVN Cluster Management API",
    description="Comprehensive API for managing KVM virtualization clusters with OVN networking",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Include routers
app.include_router(cluster.router, prefix="/api/v1/cluster", tags=["Cluster"])
app.include_router(hosts.router, prefix="/api/v1/hosts", tags=["Hosts"])
app.include_router(vms.router, prefix="/api/v1/vms", tags=["Virtual Machines"])
app.include_router(networks.router, prefix="/api/v1/networks", tags=["Networks"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "KVM/QEMU/OVN Cluster Management API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cluster": settings.cluster.name
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        workers=settings.api.workers if not settings.api.reload else 1,
        log_level=settings.api.log_level
    )
