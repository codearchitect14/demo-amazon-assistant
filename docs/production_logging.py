"""
Production-ready structured logging system for RAG pipeline with Rich integration.

This module provides comprehensive logging for production monitoring with:
- Structured JSON logging for log aggregation
- Rich console output for development/debugging
- Performance metrics and monitoring
- Error tracking and alerting
- Token usage analytics
- System health monitoring
"""

import logging
import json
import time
import sys
import os
import traceback
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
from pathlib import Path

# Rich imports
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich import box
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

# Install rich traceback for better error display
install_rich_traceback()

# Initialize console
console = Console()

# Token counting
try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
except ImportError:
    tokenizer = None
    console.print("[yellow]Warning: tiktoken not available, using character-based token estimation[/yellow]")


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories for classification."""
    PIPELINE = "pipeline"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    MEMORY = "memory"
    TOKEN = "token"
    PERFORMANCE = "performance"
    ERROR = "error"
    SECURITY = "security"
    HEALTH = "health"
    SYSTEM = "system"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    category: str
    component: str
    operation: str
    session_id: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    token_count: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class ProductionLogger:
    """
    Production-ready structured logger with Rich integration.
    """
    
    def __init__(
        self,
        name: str = "rag_pipeline",
        log_level: str = "INFO",
        enable_rich: bool = True,
        enable_file_logging: bool = True,
        enable_json_logging: bool = True,
        log_directory: str = "logs",
        max_file_size_mb: int = 100,
        backup_count: int = 5,
        include_system_metrics: bool = True
    ):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.enable_rich = enable_rich
        self.enable_file_logging = enable_file_logging
        self.enable_json_logging = enable_json_logging
        self.include_system_metrics = include_system_metrics
        
        # Setup log directory
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        # Initialize logging
        self._setup_logging()
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "total_tokens_processed": 0,
            "average_response_time_ms": 0.0,
            "error_count": 0,
            "success_count": 0
        }
        
        # Session tracking
        self.active_sessions = {}
        
        # System metrics
        self._last_system_check = 0
        self._system_metrics_cache = {}
        
        console.print(f"[green]Production Logger initialized: {name}[/green]")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        self.logger.handlers.clear()  # Clear existing handlers
        
        # Console handler with Rich
        if self.enable_rich:
            rich_handler = RichHandler(
                console=console,
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True
            )
            rich_handler.setLevel(self.log_level)
            self.logger.addHandler(rich_handler)
        
        # File handler for structured logs
        if self.enable_file_logging:
            from logging.handlers import RotatingFileHandler
            
            # JSON log file
            if self.enable_json_logging:
                json_handler = RotatingFileHandler(
                    self.log_directory / "rag_pipeline.json",
                    maxBytes=self.max_file_size_mb * 1024 * 1024,
                    backupCount=self.backup_count
                )
                json_handler.setLevel(self.log_level)
                json_handler.setFormatter(logging.Formatter('%(message)s'))
                self.logger.addHandler(json_handler)
            
            # Human-readable log file
            human_handler = RotatingFileHandler(
                self.log_directory / "rag_pipeline.log",
                maxBytes=self.max_file_size_mb * 1024 * 1024,
                backupCount=self.backup_count
            )
            human_handler.setLevel(self.log_level)
            human_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(human_handler)
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        if not self.include_system_metrics:
            return {}
        
        current_time = time.time()
        if current_time - self._last_system_check < 5:  # Cache for 5 seconds
            return self._system_metrics_cache
        
        try:
            import psutil
            
            process = psutil.Process()
            memory_info = process.memory_info()
            
            metrics = {
                "memory_usage_mb": memory_info.rss / 1024 / 1024,
                "cpu_usage_percent": process.cpu_percent(),
                "system_memory_percent": psutil.virtual_memory().percent,
                "system_cpu_percent": psutil.cpu_percent(),
                "open_files": len(process.open_files()),
                "threads": process.num_threads()
            }
            
            self._system_metrics_cache = metrics
            self._last_system_check = current_time
            return metrics
            
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}
    
    def _create_log_entry(
        self,
        level: str,
        category: str,
        component: str,
        operation: str,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        token_count: Optional[int] = None
    ) -> LogEntry:
        """Create a structured log entry."""
        system_metrics = self._get_system_metrics()
        
        return LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            category=category,
            component=component,
            operation=operation,
            session_id=session_id,
            message=message,
            data=data,
            error=error,
            duration_ms=duration_ms,
            token_count=token_count,
            memory_usage_mb=system_metrics.get("memory_usage_mb"),
            cpu_usage_percent=system_metrics.get("cpu_usage_percent")
        )
    
    def _log_structured(self, log_entry: LogEntry):
        """Log structured entry."""
        if self.enable_json_logging:
            self.logger.info(json.dumps(asdict(log_entry)))
        else:
            # Human-readable format
            msg = f"[{log_entry.category.upper()}] {log_entry.component}.{log_entry.operation}"
            if log_entry.message:
                msg += f": {log_entry.message}"
            if log_entry.session_id:
                msg += f" (session: {log_entry.session_id})"
            if log_entry.duration_ms:
                msg += f" (duration: {log_entry.duration_ms:.2f}ms)"
            if log_entry.token_count:
                msg += f" (tokens: {log_entry.token_count})"
            
            self.logger.log(getattr(logging, log_entry.level), msg)
    
    def log_pipeline_start(self, session_id: str, data: Dict[str, Any]):
        """Log pipeline start with rich display."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.PIPELINE.value,
            component="pipeline",
            operation="start",
            session_id=session_id,
            data=data
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_pipeline_start(session_id, data)
    
    def log_pipeline_end(self, session_id: str, data: Dict[str, Any], duration_ms: float):
        """Log pipeline end with rich display."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.PIPELINE.value,
            component="pipeline",
            operation="end",
            session_id=session_id,
            data=data,
            duration_ms=duration_ms
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_pipeline_end(session_id, data, duration_ms)
    
    def log_retrieval(self, session_id: str, data: Dict[str, Any], duration_ms: float):
        """Log retrieval operation."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.RETRIEVAL.value,
            component="retriever",
            operation="search",
            session_id=session_id,
            data=data,
            duration_ms=duration_ms
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_retrieval(session_id, data, duration_ms)
    
    def log_generation(self, session_id: str, data: Dict[str, Any], duration_ms: float):
        """Log generation operation."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.GENERATION.value,
            component="llm",
            operation="generate",
            session_id=session_id,
            data=data,
            duration_ms=duration_ms
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_generation(session_id, data, duration_ms)
    
    def log_token_usage(self, session_id: str, token_data: Dict[str, Any]):
        """Log token usage with detailed breakdown."""
        total_tokens = sum(token_data.values())
        
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.TOKEN.value,
            component="token_tracker",
            operation="usage",
            session_id=session_id,
            data=token_data,
            token_count=total_tokens
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_token_usage(session_id, token_data)
    
    def log_memory_operation(self, session_id: str, operation: str, data: Dict[str, Any]):
        """Log memory operation."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.MEMORY.value,
            component="memory",
            operation=operation,
            session_id=session_id,
            data=data
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_memory_operation(session_id, operation, data)
    
    def log_error(self, error: Exception, context: str = "", session_id: Optional[str] = None):
        """Log error with rich traceback."""
        log_entry = self._create_log_entry(
            level="ERROR",
            category=LogCategory.ERROR.value,
            component="system",
            operation="error",
            session_id=session_id,
            message=str(error),
            error=traceback.format_exc(),
            data={"context": context}
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_error(error, context, session_id)
    
    def log_performance(self, session_id: str, metrics: Dict[str, Any]):
        """Log performance metrics."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.PERFORMANCE.value,
            component="performance",
            operation="metrics",
            session_id=session_id,
            data=metrics
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_performance(session_id, metrics)
    
    def log_health_check(self, health_data: Dict[str, Any]):
        """Log system health check."""
        log_entry = self._create_log_entry(
            level="INFO",
            category=LogCategory.HEALTH.value,
            component="health",
            operation="check",
            data=health_data
        )
        
        self._log_structured(log_entry)
        
        if self.enable_rich:
            self._display_health_check(health_data)
    
    # Rich display methods
    def _display_pipeline_start(self, session_id: str, data: Dict[str, Any]):
        """Display pipeline start with rich formatting."""
        table = Table(title="🚀 Pipeline Start", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", session_id)
        table.add_row("Question Length", str(data.get("question_length", "N/A")))
        table.add_row("Memory Enabled", str(data.get("memory_enabled", "N/A")))
        table.add_row("Retrieval Method", str(data.get("retrieval_method", "N/A")))
        table.add_row("Model", str(data.get("model", "N/A")))
        
        console.print(table)
    
    def _display_pipeline_end(self, session_id: str, data: Dict[str, Any], duration_ms: float):
        """Display pipeline end with rich formatting."""
        table = Table(title="✅ Pipeline Complete", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", session_id)
        table.add_row("Duration", f"{duration_ms:.2f}ms")
        table.add_row("Total Tokens", str(data.get("total_tokens", "N/A")))
        table.add_row("Retrieval Performed", str(data.get("retrieval_performed", "N/A")))
        table.add_row("Response Length", str(data.get("response_length", "N/A")))
        
        console.print(table)
    
    def _display_retrieval(self, session_id: str, data: Dict[str, Any], duration_ms: float):
        """Display retrieval results."""
        table = Table(title="🔍 Retrieval Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", session_id)
        table.add_row("Duration", f"{duration_ms:.2f}ms")
        table.add_row("Documents Retrieved", str(data.get("documents_retrieved", "N/A")))
        table.add_row("Total Context Length", str(data.get("context_length", "N/A")))
        table.add_row("Retrieval Method", str(data.get("method", "N/A")))
        
        console.print(table)
    
    def _display_generation(self, session_id: str, data: Dict[str, Any], duration_ms: float):
        """Display generation results."""
        table = Table(title="🤖 Generation Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", session_id)
        table.add_row("Duration", f"{duration_ms:.2f}ms")
        table.add_row("Input Tokens", str(data.get("input_tokens", "N/A")))
        table.add_row("Output Tokens", str(data.get("output_tokens", "N/A")))
        table.add_row("Model", str(data.get("model", "N/A")))
        
        console.print(table)
    
    def _display_token_usage(self, session_id: str, token_data: Dict[str, Any]):
        """Display token usage breakdown."""
        table = Table(title="🔢 Token Usage Breakdown", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Tokens", style="yellow", justify="right")
        table.add_column("Percentage", style="magenta", justify="right")
        
        total_tokens = sum(token_data.values())
        
        for component, tokens in token_data.items():
            percentage = (tokens / total_tokens * 100) if total_tokens > 0 else 0
            table.add_row(
                component.replace("_", " ").title(),
                f"{tokens:,}",
                f"{percentage:.1f}%"
            )
        
        table.add_row("**TOTAL**", f"**{total_tokens:,}**", "**100%**")
        
        console.print(table)
    
    def _display_memory_operation(self, session_id: str, operation: str, data: Dict[str, Any]):
        """Display memory operation."""
        table = Table(title="💾 Memory Operation", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", session_id)
        table.add_row("Operation", operation)
        table.add_row("Interaction Size", f"{data.get('interaction_size_bytes', 0):,} bytes")
        table.add_row("Session Size", f"{data.get('session_size_bytes', 0):,} bytes")
        table.add_row("Total Interactions", str(data.get("total_interactions", "N/A")))
        
        console.print(table)
    
    def _display_error(self, error: Exception, context: str, session_id: Optional[str]):
        """Display error with rich formatting."""
        panel = Panel(
            f"[red]Error: {str(error)}[/red]\n"
            f"[yellow]Context: {context}[/yellow]\n"
            f"[blue]Session: {session_id or 'N/A'}[/blue]",
            title="❌ Error",
            border_style="red"
        )
        console.print(panel)
    
    def _display_performance(self, session_id: str, metrics: Dict[str, Any]):
        """Display performance metrics."""
        table = Table(title="📊 Performance Metrics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in metrics.items():
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            table.add_row(key.replace("_", " ").title(), formatted_value)
        
        console.print(table)
    
    def _display_health_check(self, health_data: Dict[str, Any]):
        """Display health check results."""
        status = health_data.get("status", "unknown")
        status_color = "green" if status == "healthy" else "red"
        
        table = Table(title="🏥 System Health", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style=status_color)
        table.add_column("Details", style="green")
        
        for component, details in health_data.items():
            if component == "status":
                continue
            if isinstance(details, dict):
                status = details.get("status", "unknown")
                details_str = str(details.get("details", ""))
            else:
                status = "unknown"
                details_str = str(details)
            table.add_row(component, status, details_str)
        
        console.print(table)
    
    @contextmanager
    def pipeline_context(self, session_id: str, data: Dict[str, Any]):
        """Context manager for pipeline operations."""
        start_time = time.time()
        self.log_pipeline_start(session_id, data)
        
        try:
            yield
        except Exception as e:
            self.log_error(e, "Pipeline execution", session_id)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.log_pipeline_end(session_id, data, duration_ms)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            "performance_metrics": self.performance_metrics,
            "active_sessions": len(self.active_sessions),
            "log_directory": str(self.log_directory),
            "log_level": logging.getLevelName(self.log_level)
        }


# Global logger instance
_production_logger = None


def get_production_logger() -> ProductionLogger:
    """Get or create global production logger instance."""
    global _production_logger
    if _production_logger is None:
        _production_logger = ProductionLogger()
    return _production_logger


def setup_production_logging(
    name: str = "rag_pipeline",
    log_level: str = "INFO",
    enable_rich: bool = True,
    enable_file_logging: bool = True,
    enable_json_logging: bool = True,
    log_directory: str = "logs"
) -> ProductionLogger:
    """Setup production logging with custom configuration."""
    global _production_logger
    _production_logger = ProductionLogger(
        name=name,
        log_level=log_level,
        enable_rich=enable_rich,
        enable_file_logging=enable_file_logging,
        enable_json_logging=enable_json_logging,
        log_directory=log_directory
    )
    return _production_logger


# Convenience functions for easy integration
def log_pipeline_start(session_id: str, data: Dict[str, Any]):
    """Log pipeline start."""
    logger = get_production_logger()
    logger.log_pipeline_start(session_id, data)


def log_pipeline_end(session_id: str, data: Dict[str, Any], duration_ms: float):
    """Log pipeline end."""
    logger = get_production_logger()
    logger.log_pipeline_end(session_id, data, duration_ms)


def log_retrieval(session_id: str, data: Dict[str, Any], duration_ms: float):
    """Log retrieval operation."""
    logger = get_production_logger()
    logger.log_retrieval(session_id, data, duration_ms)


def log_generation(session_id: str, data: Dict[str, Any], duration_ms: float):
    """Log generation operation."""
    logger = get_production_logger()
    logger.log_generation(session_id, data, duration_ms)


def log_token_usage(session_id: str, token_data: Dict[str, Any]):
    """Log token usage."""
    logger = get_production_logger()
    logger.log_token_usage(session_id, token_data)


def log_memory_operation(session_id: str, operation: str, data: Dict[str, Any]):
    """Log memory operation."""
    logger = get_production_logger()
    logger.log_memory_operation(session_id, operation, data)


def log_error(error: Exception, context: str = "", session_id: Optional[str] = None):
    """Log error."""
    logger = get_production_logger()
    logger.log_error(error, context, session_id)


def log_performance(session_id: str, metrics: Dict[str, Any]):
    """Log performance metrics."""
    logger = get_production_logger()
    logger.log_performance(session_id, metrics)


def log_health_check(health_data: Dict[str, Any]):
    """Log health check."""
    logger = get_production_logger()
    logger.log_health_check(health_data)


@contextmanager
def pipeline_context(session_id: str, data: Dict[str, Any]):
    """Context manager for pipeline operations."""
    logger = get_production_logger()
    with logger.pipeline_context(session_id, data):
        yield


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    if not text:
        return 0
    
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4


def get_logging_statistics() -> Dict[str, Any]:
    """Get logging statistics."""
    logger = get_production_logger()
    return logger.get_statistics() 