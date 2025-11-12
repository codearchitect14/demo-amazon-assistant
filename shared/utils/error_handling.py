"""
Comprehensive error handling and validation utilities.
"""

import logging
import traceback
import functools
from typing import Callable, Any, Optional, Type, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
import re
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    LLM = "llm"
    MEMORY = "memory"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors."""
    timestamp: datetime
    function_name: str
    module_name: str
    line_number: int
    severity: ErrorSeverity
    category: ErrorCategory
    user_message: str
    technical_details: str
    stack_trace: str


class RAGException(Exception):
    """Base exception for RAG system."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 category: ErrorCategory = ErrorCategory.UNKNOWN, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.severity = severity
        self.category = category
        self.context = context or self._create_context()
        self.timestamp = datetime.now()
    
    def _create_context(self) -> ErrorContext:
        """Create error context from current stack."""
        tb = traceback.extract_tb(self.__traceback__)
        if tb:
            frame = tb[-1]
            return ErrorContext(
                timestamp=datetime.now(),
                function_name=frame.name,
                module_name=frame.filename,
                line_number=frame.lineno,
                severity=self.severity,
                category=self.category,
                user_message=str(self),
                technical_details="",
                stack_trace=traceback.format_exc()
            )
        return ErrorContext(
            timestamp=datetime.now(),
            function_name="unknown",
            module_name="unknown",
            line_number=0,
            severity=self.severity,
            category=self.category,
            user_message=str(self),
            technical_details="",
            stack_trace=traceback.format_exc()
        )


class ValidationError(RAGException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = "", value: Any = None):
        super().__init__(message, ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION)
        self.field = field
        self.value = value


class NetworkError(RAGException):
    """Exception for network-related errors."""
    
    def __init__(self, message: str, url: str = "", status_code: Optional[int] = None):
        super().__init__(message, ErrorSeverity.HIGH, ErrorCategory.NETWORK)
        self.url = url
        self.status_code = status_code


class DatabaseError(RAGException):
    """Exception for database-related errors."""
    
    def __init__(self, message: str, operation: str = "", table: str = ""):
        super().__init__(message, ErrorSeverity.HIGH, ErrorCategory.DATABASE)
        self.operation = operation
        self.table = table


class LLMError(RAGException):
    """Exception for LLM-related errors."""
    
    def __init__(self, message: str, model: str = "", response: str = ""):
        super().__init__(message, ErrorSeverity.HIGH, ErrorCategory.LLM)
        self.model = model
        self.response = response


class MemoryError(RAGException):
    """Exception for memory-related errors."""
    
    def __init__(self, message: str, session_id: str = "", operation: str = ""):
        super().__init__(message, ErrorSeverity.MEDIUM, ErrorCategory.MEMORY)
        self.session_id = session_id
        self.operation = operation


class ConfigurationError(RAGException):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: str = ""):
        super().__init__(message, ErrorSeverity.CRITICAL, ErrorCategory.CONFIGURATION)
        self.config_key = config_key


class ErrorHandler:
    """Centralized error handling and logging."""
    
    @staticmethod
    def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle and log errors with context.
        
        Args:
            error: The exception to handle
            context: Additional context information
            
        Returns:
            Error response dictionary
        """
        if isinstance(error, RAGException):
            return ErrorHandler._handle_rag_error(error, context)
        else:
            return ErrorHandler._handle_generic_error(error, context)
    
    @staticmethod
    def _handle_rag_error(error: RAGException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle RAG-specific errors."""
        error_info = {
            "error_type": error.__class__.__name__,
            "message": str(error),
            "severity": error.severity.value,
            "category": error.category.value,
            "timestamp": error.timestamp.isoformat(),
            "context": context or {}
        }
        
        # Log based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error}", exc_info=True)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH ERROR: {error}", exc_info=True)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM ERROR: {error}")
        else:
            logger.info(f"LOW ERROR: {error}")
        
        return error_info
    
    @staticmethod
    def _handle_generic_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle generic Python exceptions."""
        error_info = {
            "error_type": error.__class__.__name__,
            "message": str(error),
            "severity": ErrorSeverity.HIGH.value,
            "category": ErrorCategory.UNKNOWN.value,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "stack_trace": traceback.format_exc()
        }
        
        logger.error(f"GENERIC ERROR: {error}", exc_info=True)
        return error_info


class InputValidator:
    """Comprehensive input validation utilities."""
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$')
    SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
    QUERY_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]{1,1000}$')
    
    @staticmethod
    def validate_string(value: Any, field_name: str, min_length: int = 1, max_length: int = 1000, 
                       pattern: Optional[re.Pattern] = None, allow_empty: bool = False) -> str:
        """
        Validate string input.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            min_length: Minimum length
            max_length: Maximum length
            pattern: Regex pattern to match
            allow_empty: Whether empty strings are allowed
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError(f"{field_name} cannot be None", field_name, value)
        
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field_name, value)
        
        if not allow_empty and not value.strip():
            raise ValidationError(f"{field_name} cannot be empty", field_name, value)
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters", field_name, value)
        
        if len(value) > max_length:
            raise ValidationError(f"{field_name} must be at most {max_length} characters", field_name, value)
        
        if pattern and not pattern.match(value):
            raise ValidationError(f"{field_name} format is invalid", field_name, value)
        
        return value.strip()
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_value: Optional[int] = None, 
                        max_value: Optional[int] = None) -> int:
        """
        Validate integer input.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Validated integer
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None", field_name, value)
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer", field_name, value)
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}", field_name, int_value)
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}", field_name, int_value)
        
        return int_value
    
    @staticmethod
    def validate_float(value: Any, field_name: str, min_value: Optional[float] = None, 
                      max_value: Optional[float] = None) -> float:
        """
        Validate float input.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Validated float
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None", field_name, value)
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number", field_name, value)
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}", field_name, float_value)
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}", field_name, float_value)
        
        return float_value
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str) -> bool:
        """
        Validate boolean input.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            
        Returns:
            Validated boolean
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None", field_name, value)
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValidationError(f"{field_name} must be a valid boolean", field_name, value)
    
    @staticmethod
    def validate_list(value: Any, field_name: str, min_length: int = 0, max_length: Optional[int] = None,
                     item_validator: Optional[Callable] = None) -> List[Any]:
        """
        Validate list input.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            min_length: Minimum length
            max_length: Maximum length
            item_validator: Function to validate each item
            
        Returns:
            Validated list
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None", field_name, value)
        
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"{field_name} must be a list", field_name, value)
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} must have at least {min_length} items", field_name, value)
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"{field_name} must have at most {max_length} items", field_name, value)
        
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_items.append(item_validator(item, f"{field_name}[{i}]"))
                except ValidationError as e:
                    raise ValidationError(f"Item {i} in {field_name}: {e.message}", field_name, value)
            return validated_items
        
        return list(value)
    
    @staticmethod
    def validate_dict(value: Any, field_name: str, required_keys: Optional[List[str]] = None,
                     optional_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate dictionary input.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            required_keys: Keys that must be present
            optional_keys: Keys that are allowed
            
        Returns:
            Validated dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            raise ValidationError(f"{field_name} cannot be None", field_name, value)
        
        if not isinstance(value, dict):
            raise ValidationError(f"{field_name} must be a dictionary", field_name, value)
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                raise ValidationError(f"{field_name} missing required keys: {missing_keys}", field_name, value)
        
        if optional_keys:
            invalid_keys = [key for key in value if key not in (required_keys or []) + optional_keys]
            if invalid_keys:
                raise ValidationError(f"{field_name} contains invalid keys: {invalid_keys}", field_name, value)
        
        return dict(value)
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum length
            
        Returns:
            Sanitized string
        """
        if not value:
            return ""
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(value))
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Sanitize HTML input.
        
        Args:
            value: HTML string to sanitize
            
        Returns:
            Sanitized HTML
        """
        if not value:
            return ""
        
        # Remove script tags and dangerous attributes
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized


def handle_extraction_error(func: Callable) -> Callable:
    """Decorator to handle extraction errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = ErrorHandler.handle_error(e, {"function": func.__name__})
            logger.error(f"Extraction error in {func.__name__}: {error_info}")
            return None
    return wrapper


def handle_api_error(func: Callable) -> Callable:
    """Decorator to handle API errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = ErrorHandler.handle_error(e, {"function": func.__name__})
            logger.error(f"API error in {func.__name__}: {error_info}")
            raise
    return wrapper


def handle_llm_error(func: Callable) -> Callable:
    """Decorator to handle LLM errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = ErrorHandler.handle_error(e, {"function": func.__name__})
            logger.error(f"LLM error in {func.__name__}: {error_info}")
            raise LLMError(f"LLM operation failed: {str(e)}")
    return wrapper


def handle_memory_error(func: Callable) -> Callable:
    """Decorator to handle memory errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = ErrorHandler.handle_error(e, {"function": func.__name__})
            logger.error(f"Memory error in {func.__name__}: {error_info}")
            raise MemoryError(f"Memory operation failed: {str(e)}")
    return wrapper


def safe_execute(func: Callable, *args, fallback_value: Any = None, **kwargs) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        fallback_value: Value to return on error
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or fallback value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_info = ErrorHandler.handle_error(e, {"function": func.__name__})
        logger.warning(f"Safe execute failed for {func.__name__}: {error_info}")
        return fallback_value


def validate_chat_request(query: str, session_id: Optional[str] = None, 
                         top_k: Optional[int] = None, retrieval_method: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate chat request parameters.
    
    Args:
        query: User query
        session_id: Session identifier
        top_k: Number of results to retrieve
        retrieval_method: Retrieval method
        
    Returns:
        Validated parameters
        
    Raises:
        ValidationError: If validation fails
    """
    validator = InputValidator()
    
    validated_params = {
        "query": validator.validate_string(
            query, "query", min_length=1, max_length=1000, 
            pattern=validator.QUERY_PATTERN
        ),
        "session_id": validator.validate_string(
            session_id, "session_id", min_length=1, max_length=50,
            pattern=validator.SESSION_ID_PATTERN, allow_empty=True
        ) if session_id else None,
        "top_k": validator.validate_integer(
            top_k, "top_k", min_value=1, max_value=100
        ) if top_k is not None else 5,
        "retrieval_method": validator.validate_string(
            retrieval_method, "retrieval_method", 
            min_length=1, max_length=50
        ) if retrieval_method else "title_first"
    }
    
    return validated_params 