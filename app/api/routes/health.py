"""
Health API routes for system monitoring.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
# Handle imports for different execution contexts
try:
    # Try importing as if running from root directory
    from app.services.rag_service import RAGService
except ImportError:
    # Try importing as if running from app directory
    try:
        from services.rag_service import RAGService
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
        
        from services.rag_service import RAGService
from core.container import resolve_service, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    return resolve_service(RAGService)


@router.get("/")
async def health_check_endpoint() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    try:
        logger.info("Health check requested")
        return {
            "status": "healthy",
            "message": "RAG system is operational",
            "timestamp": "2024-01-01T00:00:00Z"  # This should be actual timestamp
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
async def system_health_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Get detailed system health information.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        System health information
    """
    try:
        logger.info("System health check requested")
        return await rag_service.get_system_health()
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def performance_stats_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Get performance statistics.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Performance statistics
    """
    try:
        logger.info("Performance stats requested")
        
        # Get LLM health
        llm_health = rag_service.llm_client.get_health_status()
        
        # Get memory stats
        memory_stats = await rag_service.get_memory_stats()
        
        # Get container info
        container = get_container()
        registered_services = container.get_registered_services()
        
        return {
            "llm_health": llm_health,
            "memory_stats": memory_stats,
            "registered_services": registered_services,
            "config": {
                "memory_enabled": rag_service.config.MEMORY_ENABLED,
                "redis_enabled": rag_service.config.REDIS_ENABLED,
                "enable_circuit_breaker": rag_service.config.ENABLE_CIRCUIT_BREAKER,
                "enable_retry_logic": rag_service.config.ENABLE_RETRY_LOGIC,
            }
        }
        
    except Exception as e:
        logger.error(f"Performance stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_system_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Reset system components.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Reset result
    """
    try:
        logger.info("System reset requested")
        
        # Reset LLM health
        rag_service.llm_client.reset_health()
        
        # Reset container
        from core.container import reset_container
        reset_container()
        
        return {
            "success": True,
            "message": "System reset completed successfully",
            "components_reset": ["llm_health", "container"]
        }
        
    except Exception as e:
        logger.error(f"System reset failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/debug")
async def debug_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Get debug information for troubleshooting.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Debug information
    """
    try:
        logger.info("Debug information requested")
        
        # Get system health
        system_health = await rag_service.get_system_health()
        
        # Get memory stats
        memory_stats = await rag_service.get_memory_stats()
        
        # Get LLM health
        llm_health = rag_service.llm_client.get_health_status()
        
        # Get container info
        container = get_container()
        registered_services = container.get_registered_services()
        
        return {
            "system_health": system_health,
            "memory_stats": memory_stats,
            "llm_health": llm_health,
            "registered_services": registered_services,
            "config_summary": {
                "memory_enabled": rag_service.config.MEMORY_ENABLED,
                "redis_enabled": rag_service.config.REDIS_ENABLED,
                "enable_circuit_breaker": rag_service.config.ENABLE_CIRCUIT_BREAKER,
                "enable_retry_logic": rag_service.config.ENABLE_RETRY_LOGIC,
                "memory_max_entries": rag_service.config.MEMORY_MAX_ENTRIES,
                "memory_max_age_hours": rag_service.config.MEMORY_MAX_AGE_HOURS,
                "retry_max_attempts": rag_service.config.RETRY_MAX_ATTEMPTS,
                "circuit_breaker_failure_threshold": rag_service.config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            }
        }
        
    except Exception as e:
        logger.error(f"Debug information failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 