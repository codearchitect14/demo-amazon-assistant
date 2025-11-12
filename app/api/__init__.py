"""
API module initialization.
"""

import logging
import signal
import sys
from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# Handle imports for different execution contexts
try:
    # Try importing as if running from root directory
    from app.api.routes import chat, memory, health
    from app.config import Config
except ImportError:
    # Try importing as if running from app directory
    try:
        from routes import chat, memory, health
        from config import Config
    except ImportError:
        # Fallback: add current directory and parent to path
        import os
        import sys
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from routes import chat, memory, health
        from config import Config
from core.container import get_container

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG API",
    description="Advanced RAG system with hybrid search and memory management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create main API router
api_router = APIRouter()

# Include route modules
api_router.include_router(chat.router)
api_router.include_router(memory.router)
api_router.include_router(health.router)

# Include API routes with both prefixes for backward compatibility
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router)  # Also include without prefix for backward compatibility

# Initialize container
container = get_container()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "message": "RAG system is operational"
    }


@app.post("/reset-pipeline")
async def reset_pipeline_endpoint():
    """Reset the RAG pipeline."""
    try:
        from core.container import reset_container
        reset_container()
        logger.info("Pipeline reset successfully")
        return {"message": "Pipeline reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/pipeline")
async def debug_pipeline_endpoint():
    """Get debug information about the pipeline."""
    try:
        container = get_container()
        registered_services = container.get_registered_services()
        
        return {
            "registered_services": registered_services,
            "config": {
                "memory_enabled": Config.MEMORY_ENABLED,
                "redis_enabled": Config.REDIS_ENABLED,
                "enable_circuit_breaker": Config.ENABLE_CIRCUIT_BREAKER,
                "enable_retry_logic": Config.ENABLE_RETRY_LOGIC,
            }
        }
    except Exception as e:
        logger.error(f"Error getting pipeline debug info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if Config.LOG_LEVEL == "DEBUG" else "An unexpected error occurred"
        }
    )


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal, cleaning up...")
    try:
        # Cleanup resources
        container = get_container()
        if hasattr(container, 'cleanup'):
            container.cleanup()
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    sys.exit(0)


# Only register signal handlers when running as main module (not when imported)
if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    logger.info("Application shutting down...")
    try:
        # Cleanup resources
        container = get_container()
        if hasattr(container, 'cleanup'):
            container.cleanup()
        logger.info("Shutdown cleanup completed")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}") 