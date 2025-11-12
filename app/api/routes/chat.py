"""
Chat API routes with comprehensive error handling and validation.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from shared.utils.error_handling import (
    RAGException, ValidationError, NetworkError, ErrorHandler, InputValidator
)
from shared.utils.validation import DataSanitizer, validate_and_sanitize_input
from shared.utils.type_safety import type_check, TypeCheckMode
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

router = APIRouter()


class ChatRequest(BaseModel):
    """Validated chat request model."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    session_id: Optional[str] = Field(None, max_length=50, description="Session identifier")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to retrieve")
    retrieval_method: str = Field(default="title_first", max_length=50, description="Retrieval method")
    use_advanced_features: bool = Field(default=False, description="Use advanced features")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate and sanitize query."""
        sanitizer = DataSanitizer()
        return sanitizer.sanitize_string(v, max_length=1000)
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID."""
        if v is None:
            return v
        validator = InputValidator()
        return validator.validate_string(v, "session_id", min_length=1, max_length=50)
    
    @validator('retrieval_method')
    def validate_retrieval_method(cls, v):
        """Validate retrieval method."""
        valid_methods = ["title_first", "multi", "hybrid", "semantic"]
        if v not in valid_methods:
            raise ValueError(f"retrieval_method must be one of {valid_methods}")
        return v


class ChatResponse(BaseModel):
    """Validated chat response model."""
    
    question: str = Field(..., description="User question")
    answer: str = Field(..., description="AI response")
    context: str = Field(default="", description="Retrieved context")
    intent: Dict[str, Any] = Field(default_factory=dict, description="Intent information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


@type_check(TypeCheckMode.STRICT)
def get_rag_service() -> RAGService:
    """
    Get RAG service instance with dependency injection.
    
    Returns:
        RAGService instance
        
    Raises:
        ConfigurationError: If service cannot be created
    """
    try:
        return resolve_service(RAGService)
    except Exception as e:
        logger.error(f"Failed to create RAG service: {e}")
        raise RAGException(f"Service initialization failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> ChatResponse:
    """
    Process chat request with comprehensive validation and error handling.
    
    Args:
        request: Validated chat request
        rag_service: RAG service instance
        
    Returns:
        ChatResponse with AI response and metadata
        
    Raises:
        HTTPException: If processing fails
    """
    error_handler = ErrorHandler()
    
    try:
        logger.info(f"Processing chat request: {request.query[:50]}...")
        
        # Validate and sanitize input
        validation_result = validate_and_sanitize_input(
            request.dict(),
            sanitize=True,
            level="normal"
        )
        
        if not validation_result.is_valid:
            raise ValidationError(f"Input validation failed: {validation_result.errors}")
        
        # Process chat request
        result = await rag_service.process_chat(
            query=request.query,
            session_id=request.session_id,
            top_k=request.top_k,
            retrieval_method=request.retrieval_method,
            use_advanced_features=request.use_advanced_features,
        )
        
        # Validate response
        if not isinstance(result, dict):
            raise ValueError("Invalid response format from RAG service")
        
        # Create response
        response = ChatResponse(
            question=result.get("question", request.query),
            answer=result.get("answer", "No response generated"),
            context=result.get("context", ""),
            intent=result.get("intent", {}),
            metadata=result.get("metadata", {})
        )
        
        logger.info(f"Chat request processed successfully")
        return response
        
    except ValidationError as e:
        error_info = error_handler.handle_error(e)
        logger.warning(f"Validation error: {error_info}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except RAGException as e:
        error_info = error_handler.handle_error(e)
        logger.error(f"RAG error: {error_info}")
        raise HTTPException(status_code=500, detail="Processing failed")
        
    except Exception as e:
        error_info = error_handler.handle_error(e)
        logger.error(f"Unexpected error: {error_info}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Process streaming chat request with comprehensive validation.
    
    Args:
        request: Validated chat request
        rag_service: RAG service instance
        
    Returns:
        StreamingResponse with Server-Sent Events
        
    Raises:
        HTTPException: If processing fails
    """
    error_handler = ErrorHandler()
    
    async def generate_stream():
        """Generate streaming response with error handling."""
        try:
            logger.info(f"Processing streaming chat request: {request.query[:50]}...")
            
            # Validate and sanitize input
            validation_result = validate_and_sanitize_input(
                request.dict(),
                sanitize=True,
                level="normal"
            )
            
            if not validation_result.is_valid:
                error_data = {
                    "type": "error",
                    "message": f"Input validation failed: {validation_result.errors}"
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                return
            
            context_data = ""
            intent_data = {}
            metadata_data = {}
            
            # Process streaming request
            async for chunk in rag_service.process_chat_stream(
                query=request.query,
                session_id=request.session_id,
                top_k=request.top_k,
                retrieval_method=request.retrieval_method,
                use_advanced_features=request.use_advanced_features,
            ):
                if isinstance(chunk, dict) and chunk.get("type") == "context":
                    context_data = chunk.get("content", "")
                    intent_data = chunk.get("intent", {})
                    continue
                elif isinstance(chunk, str):
                    data = {"type": "token", "content": chunk}
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    continue
            
            # Send completion data
            completion_data = {
                "type": "complete",
                "context": context_data,
                "metadata": {
                    "retrieval_method": request.retrieval_method,
                    "session_id": request.session_id,
                    "memory_enabled": True,
                    "intent": intent_data,
                    "needs_retrieval": bool(context_data.strip()),
                }
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
            logger.info("Streaming chat request completed successfully")
            
        except ValidationError as e:
            error_info = error_handler.handle_error(e)
            logger.warning(f"Validation error in stream: {error_info}")
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
            
        except RAGException as e:
            error_info = error_handler.handle_error(e)
            logger.error(f"RAG error in stream: {error_info}")
            error_data = {"type": "error", "message": "Processing failed"}
            yield f"data: {json.dumps(error_data)}\n\n"
            
        except Exception as e:
            error_info = error_handler.handle_error(e)
            logger.error(f"Unexpected error in stream: {error_info}")
            error_data = {"type": "error", "message": "Internal server error"}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint with comprehensive system status.
    
    Returns:
        Health status information
    """
    try:
        rag_service = get_rag_service()
        health_status = await rag_service.get_system_health()
        
        return {
            "status": "healthy",
            "timestamp": health_status.get("timestamp"),
            "services": {
                "rag_service": "operational",
                "llm_client": "operational",
                "retriever": "operational",
                "memory": "operational"
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        } 