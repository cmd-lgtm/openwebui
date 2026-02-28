"""
NexusAI IDE - Main FastAPI Application
World-class AI-powered IDE backend with multi-provider support
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.routes import chat, providers, models, files, auth, settings
from app.core.config import settings as app_settings
from app.core.exceptions import NexusAIException
from app.db.database import create_tables
from app.cache import init_cache, close_cache
from app.queue import init_queue, close_queue, QueueWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Queue worker instance
queue_worker: QueueWorker = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler"""
    logger.info("🚀 Starting NexusAI IDE Backend...")

    # Initialize Redis cache
    await init_cache()
    logger.info("✅ Cache initialized")

    # Initialize queue
    await init_queue()

    # Start queue worker
    global queue_worker
    queue_worker = QueueWorker(["code_execution", "file_indexing"])
    await queue_worker.start()

    # Create database tables
    await create_tables()
    logger.info("✅ Database tables initialized")

    yield

    # Cleanup
    if queue_worker:
        await queue_worker.stop()
    await close_queue()
    await close_cache()
    logger.info("🛑 Shutting down NexusAI IDE Backend...")


# Create FastAPI application
app = FastAPI(
    title="NexusAI IDE API",
    description="AI-Powered IDE with local and web AI capabilities",
    version="2.0.0",
    docs_url="/docs" if app_settings.DEBUG else None,
    redoc_url="/redoc" if app_settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if app_settings.DEBUG else ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(NexusAIException)
async def nexus_ai_exception_handler(request: Request, exc: NexusAIException):
    """Handle custom NexusAI exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if app_settings.DEBUG else None
            }
        }
    )


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint with cache and queue status"""
    from app.cache import cache_service
    from app.queue import queue_service

    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "cache": "enabled" if cache_service.is_enabled else "disabled",
            "queue": "enabled" if queue_service.is_enabled else "disabled",
        }
    }


# Mount API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["Providers"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])


@app.get("/api/v1")
async def api_root():
    """API root endpoint"""
    return {
        "name": "NexusAI IDE API",
        "version": "2.0.0",
        "docs": "/docs" if app_settings.DEBUG else None,
        "features": {
            "local_ai": True,
            "web_ai": True,
            "code_execution": True,
            "rag": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=app_settings.DEBUG,
        log_level="info"
    )
