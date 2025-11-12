"""
Memory API routes for conversation memory operations.
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
from core.container import resolve_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    return resolve_service(RAGService)


@router.get("/stats")
async def memory_stats_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Get memory statistics.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Memory statistics
    """
    try:
        logger.info("Getting memory statistics")
        return await rag_service.get_memory_stats()
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session_memory_endpoint(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Clear memory for a specific session.
    
    Args:
        session_id: Session identifier
        rag_service: RAG service instance
        
    Returns:
        Operation result
    """
    try:
        logger.info(f"Clearing memory for session: {session_id}")
        return await rag_service.clear_session_memory(session_id)
    except Exception as e:
        logger.error(f"Error clearing session memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_session_history_endpoint(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        rag_service: RAG service instance
        
    Returns:
        Conversation history
    """
    try:
        logger.info(f"Getting conversation history for session: {session_id}")
        return await rag_service.get_conversation_history(session_id)
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_memory_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Test memory functionality.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Test result
    """
    try:
        logger.info("Testing memory functionality")
        
        # Test adding an interaction
        test_session_id = "test_session_123"
        test_question = "What is this test?"
        test_answer = "This is a test response."
        
        # Add test interaction
        await rag_service.memory.add_interaction_async(
            test_session_id, test_question, test_answer
        )
        
        # Get recent context
        recent_context = await rag_service.memory.get_recent_context_async(test_session_id)
        
        # Clear test session
        await rag_service.memory.clear_session_async(test_session_id)
        
        return {
            "success": True,
            "message": "Memory test completed successfully",
            "test_session_id": test_session_id,
            "interactions_added": 1,
            "recent_context_count": len(recent_context)
        }
        
    except Exception as e:
        logger.error(f"Error in memory test: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/test-prompt")
async def test_prompt_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Test prompt generation functionality.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Test result
    """
    try:
        logger.info("Testing prompt generation")
        
        # Test prompt generation
        test_context = "This is a test context with product information."
        test_question = "What products are available?"
        test_history = "Previous question: What is this?\nPrevious answer: This is a test."
        
        from prompts import build_rag_user_prompt, get_rag_system_prompt
        
        user_prompt = build_rag_user_prompt(test_context, test_question, test_history)
        system_prompt = get_rag_system_prompt()
        
        return {
            "success": True,
            "message": "Prompt generation test completed successfully",
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt),
            "system_prompt_preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
            "user_prompt_preview": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
        }
        
    except Exception as e:
        logger.error(f"Error in prompt test: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/debug")
async def memory_debug_endpoint(
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Get detailed memory debug information.
    
    Args:
        rag_service: RAG service instance
        
    Returns:
        Debug information
    """
    try:
        logger.info("Getting memory debug information")
        
        # Get memory stats
        memory_stats = await rag_service.get_memory_stats()
        
        # Get system health
        system_health = await rag_service.get_system_health()
        
        return {
            "memory_stats": memory_stats,
            "system_health": system_health,
            "memory_type": type(rag_service.memory).__name__,
            "config": {
                "memory_enabled": rag_service.config.MEMORY_ENABLED,
                "memory_max_entries": rag_service.config.MEMORY_MAX_ENTRIES,
                "memory_max_age_hours": rag_service.config.MEMORY_MAX_AGE_HOURS,
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting memory debug info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 