"""
Integration module for production logging with the RAG pipeline.

This module provides seamless integration between the production logging system
and the existing RAG pipeline components.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
import traceback

# Import production logging
try:
    from production_logging import (
        get_production_logger, log_pipeline_start, log_pipeline_end,
        log_retrieval, log_generation, log_token_usage, log_memory_operation,
        log_error, log_performance, log_health_check, pipeline_context,
        count_tokens
    )
except ImportError:
    # Fallback if production_logging is not available
    def get_production_logger():
        return None
    
    def log_pipeline_start(*args, **kwargs):
        pass
    
    def log_pipeline_end(*args, **kwargs):
        pass
    
    def log_retrieval(*args, **kwargs):
        pass
    
    def log_generation(*args, **kwargs):
        pass
    
    def log_token_usage(*args, **kwargs):
        pass
    
    def log_memory_operation(*args, **kwargs):
        pass
    
    def log_error(*args, **kwargs):
        pass
    
    def log_performance(*args, **kwargs):
        pass
    
    def log_health_check(*args, **kwargs):
        pass
    
    def pipeline_context(*args, **kwargs):
        from contextlib import nullcontext
        return nullcontext()
    
    def count_tokens(text: str) -> int:
        return len(text) // 4 if text else 0


class RAGLoggingIntegration:
    """
    Integration class for RAG pipeline logging.
    """
    
    def __init__(self):
        self.logger = get_production_logger()
        self.active_sessions = {}
    
    def log_rag_pipeline_start(self, session_id: str, question: str, **kwargs):
        """Log RAG pipeline start."""
        data = {
            "question_length": len(question),
            "question_preview": question[:100] + "..." if len(question) > 100 else question,
            **kwargs
        }
        log_pipeline_start(session_id, data)
        self.active_sessions[session_id] = {"start_time": time.time()}
    
    def log_rag_pipeline_end(self, session_id: str, result: Dict[str, Any], **kwargs):
        """Log RAG pipeline end."""
        if session_id in self.active_sessions:
            duration_ms = (time.time() - self.active_sessions[session_id]["start_time"]) * 1000
            del self.active_sessions[session_id]
        else:
            duration_ms = 0
        
        data = {
            "total_tokens": result.get("total_tokens", 0),
            "retrieval_performed": result.get("retrieval_performed", False),
            "response_length": len(result.get("answer", "")),
            "response_preview": result.get("answer", "")[:100] + "..." if len(result.get("answer", "")) > 100 else result.get("answer", ""),
            **kwargs
        }
        log_pipeline_end(session_id, data, duration_ms)
    
    def log_retrieval_operation(self, session_id: str, query: str, results: list, duration_ms: float, **kwargs):
        """Log retrieval operation."""
        data = {
            "query": query,
            "documents_retrieved": len(results),
            "context_length": sum(len(str(r)) for r in results),
            "method": kwargs.get("method", "unknown"),
            **kwargs
        }
        log_retrieval(session_id, data, duration_ms)
    
    def log_generation_operation(self, session_id: str, prompt: str, response: str, duration_ms: float, **kwargs):
        """Log generation operation."""
        data = {
            "input_tokens": count_tokens(prompt),
            "output_tokens": count_tokens(response),
            "model": kwargs.get("model", "unknown"),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "response_preview": response[:200] + "..." if len(response) > 200 else response,
            **kwargs
        }
        log_generation(session_id, data, duration_ms)
    
    def log_token_breakdown(self, session_id: str, token_data: Dict[str, int]):
        """Log token usage breakdown."""
        log_token_usage(session_id, token_data)
    
    def log_memory_operation(self, session_id: str, operation: str, data: Dict[str, Any]):
        """Log memory operation."""
        log_memory_operation(session_id, operation, data)
    
    def log_error_with_context(self, error: Exception, context: str = "", session_id: Optional[str] = None):
        """Log error with context."""
        log_error(error, context, session_id)
    
    def log_performance_metrics(self, session_id: str, metrics: Dict[str, Any]):
        """Log performance metrics."""
        log_performance(session_id, metrics)
    
    def log_health_status(self, health_data: Dict[str, Any]):
        """Log health status."""
        log_health_check(health_data)


# Global integration instance
_rag_logging_integration = None


def get_rag_logging_integration() -> RAGLoggingIntegration:
    """Get or create global RAG logging integration instance."""
    global _rag_logging_integration
    if _rag_logging_integration is None:
        _rag_logging_integration = RAGLoggingIntegration()
    return _rag_logging_integration


def with_logging(func: Callable) -> Callable:
    """
    Decorator to add logging to RAG pipeline functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        integration = get_rag_logging_integration()
        
        # Extract session_id from kwargs or first argument
        session_id = kwargs.get("session_id", "unknown")
        if args and hasattr(args[0], "session_id"):
            session_id = args[0].session_id
        
        # Log function start
        integration.log_rag_pipeline_start(
            session_id,
            kwargs.get("question", "unknown"),
            function_name=func.__name__,
            **kwargs
        )
        
        try:
            result = func(*args, **kwargs)
            
            # Log function end
            integration.log_rag_pipeline_end(
                session_id,
                result if isinstance(result, dict) else {"result": str(result)},
                function_name=func.__name__
            )
            
            return result
            
        except Exception as e:
            integration.log_error_with_context(e, f"Function {func.__name__}", session_id)
            raise
    
    return wrapper


def with_async_logging(func: Callable) -> Callable:
    """
    Decorator to add logging to async RAG pipeline functions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        integration = get_rag_logging_integration()
        
        # Extract session_id from kwargs or first argument
        session_id = kwargs.get("session_id", "unknown")
        if args and hasattr(args[0], "session_id"):
            session_id = args[0].session_id
        
        # Log function start
        integration.log_rag_pipeline_start(
            session_id,
            kwargs.get("question", "unknown"),
            function_name=func.__name__,
            **kwargs
        )
        
        try:
            result = await func(*args, **kwargs)
            
            # Log function end
            integration.log_rag_pipeline_end(
                session_id,
                result if isinstance(result, dict) else {"result": str(result)},
                function_name=func.__name__
            )
            
            return result
            
        except Exception as e:
            integration.log_error_with_context(e, f"Async function {func.__name__}", session_id)
            raise
    
    return wrapper


def log_retrieval_operation(session_id: str, query: str, results: list, duration_ms: float, **kwargs):
    """Log retrieval operation."""
    integration = get_rag_logging_integration()
    integration.log_retrieval_operation(session_id, query, results, duration_ms, **kwargs)


def log_generation_operation(session_id: str, prompt: str, response: str, duration_ms: float, **kwargs):
    """Log generation operation."""
    integration = get_rag_logging_integration()
    integration.log_generation_operation(session_id, prompt, response, duration_ms, **kwargs)


def log_token_breakdown(session_id: str, token_data: Dict[str, int]):
    """Log token usage breakdown."""
    integration = get_rag_logging_integration()
    integration.log_token_breakdown(session_id, token_data)


def log_memory_operation(session_id: str, operation: str, data: Dict[str, Any]):
    """Log memory operation."""
    integration = get_rag_logging_integration()
    integration.log_memory_operation(session_id, operation, data)


def log_error_with_context(error: Exception, context: str = "", session_id: Optional[str] = None):
    """Log error with context."""
    integration = get_rag_logging_integration()
    integration.log_error_with_context(error, context, session_id)


def log_performance_metrics(session_id: str, metrics: Dict[str, Any]):
    """Log performance metrics."""
    integration = get_rag_logging_integration()
    integration.log_performance_metrics(session_id, metrics)


def log_health_status(health_data: Dict[str, Any]):
    """Log health status."""
    integration = get_rag_logging_integration()
    integration.log_health_status(health_data)


# Integration with existing RAG pipeline
def integrate_with_rag_pipeline():
    """
    Integrate logging with existing RAG pipeline components.
    This function should be called during system initialization.
    """
    try:
        # Import RAG pipeline components
        from rag.rag_pipeline import RAGPipeline
        from rag.rag_utils import logger as rag_logger
        
        # Replace the default logger with production logger
        production_logger = get_production_logger()
        if production_logger:
            # Update the RAG pipeline logger
            rag_logger.handlers.clear()
            rag_logger.addHandler(production_logger.logger.handlers[0])
            
            print("✅ Production logging integrated with RAG pipeline")
        else:
            print("⚠️ Production logger not available, using default logging")
            
    except ImportError as e:
        print(f"⚠️ Could not integrate with RAG pipeline: {e}")
    except Exception as e:
        print(f"❌ Error integrating logging: {e}")


# Convenience function for quick setup
def setup_rag_logging(
    log_level: str = "INFO",
    enable_rich: bool = True,
    enable_file_logging: bool = True,
    enable_json_logging: bool = True,
    log_directory: str = "logs"
):
    """
    Setup RAG logging with production configuration.
    """
    from production_logging import setup_production_logging
    
    # Setup production logging
    logger = setup_production_logging(
        name="rag_pipeline",
        log_level=log_level,
        enable_rich=enable_rich,
        enable_file_logging=enable_file_logging,
        enable_json_logging=enable_json_logging,
        log_directory=log_directory
    )
    
    # Integrate with RAG pipeline
    integrate_with_rag_pipeline()
    
    return logger 