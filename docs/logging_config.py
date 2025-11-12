"""
Structured logging configuration for the RAG system.

This module provides logging configuration for monitoring the context optimization
and overall system performance.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging that outputs JSON format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'component'):
            log_entry['component'] = record.component
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'memory_type'):
            log_entry['memory_type'] = record.memory_type
        if hasattr(record, 'optimization'):
            log_entry['optimization'] = record.optimization
        if hasattr(record, 'processing_time_ms'):
            log_entry['processing_time_ms'] = record.processing_time_ms
        if hasattr(record, 'context_length'):
            log_entry['context_length'] = record.context_length
        if hasattr(record, 'conversation_length'):
            log_entry['conversation_length'] = record.conversation_length
        if hasattr(record, 'interaction_size_bytes'):
            log_entry['interaction_size_bytes'] = record.interaction_size_bytes
        if hasattr(record, 'context_saved_bytes'):
            log_entry['context_saved_bytes'] = record.context_saved_bytes
        if hasattr(record, 'total_time_ms'):
            log_entry['total_time_ms'] = record.total_time_ms
        if hasattr(record, 'retrieval_performed'):
            log_entry['retrieval_performed'] = record.retrieval_performed
        if hasattr(record, 'conversation_only_mode'):
            log_entry['conversation_only_mode'] = record.conversation_only_mode
        if hasattr(record, 'should_retrieve'):
            log_entry['should_retrieve'] = record.should_retrieve
        if hasattr(record, 'error'):
            log_entry['error'] = record.error
            
        return json.dumps(log_entry)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Base format
        formatted = f"[{self.formatTime(record)}] {record.levelname} - {record.name}: {record.getMessage()}"
        
        # Add structured fields in a readable format
        extra_fields = []
        
        if hasattr(record, 'component'):
            extra_fields.append(f"component={record.component}")
        if hasattr(record, 'operation'):
            extra_fields.append(f"operation={record.operation}")
        if hasattr(record, 'session_id'):
            extra_fields.append(f"session={record.session_id}")
        if hasattr(record, 'memory_type'):
            extra_fields.append(f"memory={record.memory_type}")
        if hasattr(record, 'optimization'):
            extra_fields.append(f"optimization={record.optimization}")
        if hasattr(record, 'processing_time_ms'):
            extra_fields.append(f"time={record.processing_time_ms}ms")
        if hasattr(record, 'context_length'):
            extra_fields.append(f"context={record.context_length}chars")
        if hasattr(record, 'conversation_length'):
            extra_fields.append(f"history={record.conversation_length}chars")
        if hasattr(record, 'interaction_size_bytes'):
            extra_fields.append(f"size={record.interaction_size_bytes}B")
        if hasattr(record, 'context_saved_bytes'):
            extra_fields.append(f"saved={record.context_saved_bytes}B")
        if hasattr(record, 'total_time_ms'):
            extra_fields.append(f"total={record.total_time_ms}ms")
        if hasattr(record, 'retrieval_performed'):
            extra_fields.append(f"retrieval={record.retrieval_performed}")
        if hasattr(record, 'conversation_only_mode'):
            extra_fields.append(f"conversation_only={record.conversation_only_mode}")
        if hasattr(record, 'should_retrieve'):
            extra_fields.append(f"should_retrieve={record.should_retrieve}")
        if hasattr(record, 'error'):
            extra_fields.append(f"error={record.error}")
            
        if extra_fields:
            formatted += f" ({', '.join(extra_fields)})"
            
        return formatted


def setup_logging(
    level: str = "INFO",
    format_type: str = "human",  # "human" or "json"
    output_file: str = None,
    enable_console: bool = True
) -> None:
    """
    Setup structured logging for the RAG system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Output format ("human" or "json")
        output_file: Optional file path for log output
        enable_console: Whether to enable console output
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if format_type == "json":
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if output_file:
        file_handler = logging.FileHandler(output_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized", extra={
        "component": "logging",
        "operation": "setup",
        "level": level,
        "format_type": format_type,
        "output_file": output_file,
        "enable_console": enable_console
    })


def log_memory_stats(memory, session_id: str = None) -> None:
    """
    Log memory statistics for monitoring.
    
    Args:
        memory: Memory object to get stats from
        session_id: Optional session ID for specific session stats
    """
    try:
        stats = memory.get_memory_stats()
        logger = logging.getLogger(__name__)
        
        logger.info("Memory statistics", extra={
            "component": "memory",
            "operation": "stats",
            "memory_type": stats.get("memory_type", "unknown"),
            "total_sessions": stats.get("total_sessions", 0),
            "total_interactions": stats.get("total_interactions", 0),
            "total_memory_bytes": stats.get("total_memory_bytes", 0),
            "optimization": stats.get("optimization", "unknown"),
            "session_id": session_id
        })
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("Error getting memory stats", extra={
            "component": "memory",
            "operation": "stats_error",
            "error": str(e),
            "session_id": session_id
        })


def log_pipeline_performance(
    session_id: str,
    total_time_ms: float,
    retrieval_performed: bool,
    conversation_only_mode: bool,
    context_length: int = 0,
    conversation_length: int = 0,
    answer_length: int = 0
) -> None:
    """
    Log pipeline performance metrics.
    
    Args:
        session_id: Session ID
        total_time_ms: Total processing time in milliseconds
        retrieval_performed: Whether retrieval was performed
        conversation_only_mode: Whether conversation-only mode was used
        context_length: Length of retrieved context
        conversation_length: Length of conversation history
        answer_length: Length of generated answer
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Pipeline performance metrics", extra={
        "component": "rag_pipeline",
        "operation": "performance",
        "session_id": session_id,
        "total_time_ms": total_time_ms,
        "retrieval_performed": retrieval_performed,
        "conversation_only_mode": conversation_only_mode,
        "context_length": context_length,
        "conversation_length": conversation_length,
        "answer_length": answer_length,
        "optimization": "context_optimization_enabled"
    })


# Example usage
if __name__ == "__main__":
    # Setup logging for development
    setup_logging(
        level="INFO",
        format_type="human",
        enable_console=True
    )
    
    # Example log messages
    logger = logging.getLogger("example")
    
    logger.info("Example memory operation", extra={
        "component": "memory",
        "operation": "add_interaction",
        "session_id": "test_session_123",
        "memory_type": "in_memory",
        "optimization": "context_not_stored",
        "processing_time_ms": 45.2,
        "interaction_size_bytes": 1024,
        "context_saved_bytes": 5000
    })
    
    logger.info("Example pipeline operation", extra={
        "component": "rag_pipeline",
        "operation": "complete",
        "session_id": "test_session_123",
        "total_time_ms": 1250.5,
        "retrieval_performed": True,
        "conversation_only_mode": False,
        "context_length": 2500,
        "conversation_length": 800,
        "answer_length": 450
    }) 