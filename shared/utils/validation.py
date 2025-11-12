"""
Comprehensive input validation and data sanitization system.
"""

import re
import json
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ValidationLevel(Enum):
    """Validation levels."""
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    value: Any
    errors: List[str]
    warnings: List[str]
    sanitized: bool = False


class DataSanitizer:
    """Data sanitization utilities."""
    
    # HTML entities to escape
    HTML_ENTITIES = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\')',
        r'(\b(OR|AND)\b\s+\d+\s*LIKE\s*\'[^\']*\')',
        r'(\b(OR|AND)\b\s+\d+\s*IN\s*\([^)]*\))',
        r'(\b(OR|AND)\b\s+\d+\s*BETWEEN\s+\d+\s+AND\s+\d+)',
        r'(\b(OR|AND)\b\s+\d+\s*EXISTS\s*\([^)]*\))',
        r'(\b(OR|AND)\b\s+\d+\s*NOT\s+EXISTS\s*\([^)]*\))',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<applet[^>]*>.*?</applet>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<textarea[^>]*>.*?</textarea>',
        r'<select[^>]*>.*?</select>',
        r'<button[^>]*>.*?</button>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'<link[^>]*>',
        r'<base[^>]*>',
        r'<bgsound[^>]*>',
        r'<marquee[^>]*>.*?</marquee>',
        r'<title[^>]*>.*?</title>',
        r'<xmp[^>]*>.*?</xmp>',
        r'<plaintext[^>]*>.*?</plaintext>',
        r'<listing[^>]*>.*?</listing>',
        r'<nobr[^>]*>.*?</nobr>',
        r'<noembed[^>]*>.*?</noembed>',
        r'<noframes[^>]*>.*?</noframes>',
        r'<noscript[^>]*>.*?</noscript>',
        r'<wbr[^>]*>',
        r'<xmp[^>]*>.*?</xmp>',
        r'<plaintext[^>]*>.*?</plaintext>',
        r'<listing[^>]*>.*?</listing>',
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """
        Sanitize string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum length
            allow_html: Whether to allow HTML tags
            
        Returns:
            Sanitized string
        """
        if not value:
            return ""
        
        # Convert to string
        sanitized = str(value)
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Remove SQL injection patterns
        for pattern in DataSanitizer.SQL_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Remove XSS patterns if HTML not allowed
        if not allow_html:
            for pattern in DataSanitizer.XSS_PATTERNS:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML escape if not allowing HTML
        if not allow_html:
            sanitized = html.escape(sanitized)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL input.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
        """
        if not url:
            return ""
        
        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Only allow http and https
            if parsed.scheme not in ('http', 'https'):
                return ""
            
            # Reconstruct URL
            sanitized = urllib.parse.urlunparse(parsed)
            
            return sanitized
        except Exception:
            return ""
    
    @staticmethod
    def sanitize_json(data: Any) -> str:
        """
        Sanitize JSON data.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized JSON string
        """
        try:
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        except Exception:
            return "{}"
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize email address.
        
        Args:
            email: Email to sanitize
            
        Returns:
            Sanitized email
        """
        if not email:
            return ""
        
        # Basic email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        sanitized = email.strip().lower()
        
        if not email_pattern.match(sanitized):
            return ""
        
        return sanitized
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return ""
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:255-len(ext)-1] + ('.' + ext if ext else '')
        
        return sanitized.strip()


class TypeValidator:
    """Type validation utilities."""
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, field_name: str) -> Any:
        """
        Validate type of value.
        
        Args:
            value: Value to validate
            expected_type: Expected type
            field_name: Field name for error messages
            
        Returns:
            Validated value
            
        Raises:
            TypeError: If type validation fails
        """
        if not isinstance(value, expected_type):
            raise TypeError(f"{field_name} must be of type {expected_type.__name__}, got {type(value).__name__}")
        
        return value
    
    @staticmethod
    def validate_optional_type(value: Any, expected_type: type, field_name: str) -> Optional[Any]:
        """
        Validate optional type of value.
        
        Args:
            value: Value to validate
            expected_type: Expected type
            field_name: Field name for error messages
            
        Returns:
            Validated value or None
            
        Raises:
            TypeError: If type validation fails
        """
        if value is None:
            return None
        
        return TypeValidator.validate_type(value, expected_type, field_name)
    
    @staticmethod
    def validate_union_type(value: Any, expected_types: List[type], field_name: str) -> Any:
        """
        Validate union type of value.
        
        Args:
            value: Value to validate
            expected_types: List of expected types
            field_name: Field name for error messages
            
        Returns:
            Validated value
            
        Raises:
            TypeError: If type validation fails
        """
        for expected_type in expected_types:
            if isinstance(value, expected_type):
                return value
        
        type_names = [t.__name__ for t in expected_types]
        raise TypeError(f"{field_name} must be one of {type_names}, got {type(value).__name__}")


class SchemaValidator:
    """Schema-based validation."""
    
    @staticmethod
    def validate_dict_schema(data: Dict[str, Any], schema: Dict[str, Any], 
                           field_name: str = "data") -> Dict[str, Any]:
        """
        Validate dictionary against schema.
        
        Args:
            data: Data to validate
            schema: Schema definition
            field_name: Field name for error messages
            
        Returns:
            Validated data
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValueError(f"{field_name} must be a dictionary")
        
        validated = {}
        
        for key, schema_def in schema.items():
            if key not in data:
                if schema_def.get("required", False):
                    raise ValueError(f"Required field '{key}' missing in {field_name}")
                continue
            
            value = data[key]
            validated[key] = SchemaValidator._validate_field(
                value, schema_def, f"{field_name}.{key}"
            )
        
        return validated
    
    @staticmethod
    def _validate_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> Any:
        """Validate individual field."""
        field_type = schema_def.get("type")
        
        if field_type == "string":
            return SchemaValidator._validate_string_field(value, schema_def, field_path)
        elif field_type == "integer":
            return SchemaValidator._validate_integer_field(value, schema_def, field_path)
        elif field_type == "float":
            return SchemaValidator._validate_float_field(value, schema_def, field_path)
        elif field_type == "boolean":
            return SchemaValidator._validate_boolean_field(value, schema_def, field_path)
        elif field_type == "list":
            return SchemaValidator._validate_list_field(value, schema_def, field_path)
        elif field_type == "dict":
            return SchemaValidator._validate_dict_field(value, schema_def, field_path)
        else:
            raise ValueError(f"Unknown field type '{field_type}' in {field_path}")
    
    @staticmethod
    def _validate_string_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> str:
        """Validate string field."""
        if not isinstance(value, str):
            raise ValueError(f"{field_path} must be a string")
        
        min_length = schema_def.get("min_length", 0)
        max_length = schema_def.get("max_length")
        pattern = schema_def.get("pattern")
        
        if len(value) < min_length:
            raise ValueError(f"{field_path} must be at least {min_length} characters")
        
        if max_length and len(value) > max_length:
            raise ValueError(f"{field_path} must be at most {max_length} characters")
        
        if pattern and not re.match(pattern, value):
            raise ValueError(f"{field_path} format is invalid")
        
        return value
    
    @staticmethod
    def _validate_integer_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> int:
        """Validate integer field."""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_path} must be an integer")
        
        min_value = schema_def.get("min_value")
        max_value = schema_def.get("max_value")
        
        if min_value is not None and int_value < min_value:
            raise ValueError(f"{field_path} must be at least {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValueError(f"{field_path} must be at most {max_value}")
        
        return int_value
    
    @staticmethod
    def _validate_float_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> float:
        """Validate float field."""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_path} must be a number")
        
        min_value = schema_def.get("min_value")
        max_value = schema_def.get("max_value")
        
        if min_value is not None and float_value < min_value:
            raise ValueError(f"{field_path} must be at least {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValueError(f"{field_path} must be at most {max_value}")
        
        return float_value
    
    @staticmethod
    def _validate_boolean_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> bool:
        """Validate boolean field."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        raise ValueError(f"{field_path} must be a boolean")
    
    @staticmethod
    def _validate_list_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> List[Any]:
        """Validate list field."""
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{field_path} must be a list")
        
        min_length = schema_def.get("min_length", 0)
        max_length = schema_def.get("max_length")
        item_schema = schema_def.get("items")
        
        if len(value) < min_length:
            raise ValueError(f"{field_path} must have at least {min_length} items")
        
        if max_length and len(value) > max_length:
            raise ValueError(f"{field_path} must have at most {max_length} items")
        
        if item_schema:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_items.append(
                        SchemaValidator._validate_field(item, item_schema, f"{field_path}[{i}]")
                    )
                except ValueError as e:
                    raise ValueError(f"Item {i} in {field_path}: {str(e)}")
            return validated_items
        
        return list(value)
    
    @staticmethod
    def _validate_dict_field(value: Any, schema_def: Dict[str, Any], field_path: str) -> Dict[str, Any]:
        """Validate dictionary field."""
        if not isinstance(value, dict):
            raise ValueError(f"{field_path} must be a dictionary")
        
        properties = schema_def.get("properties", {})
        required = schema_def.get("required", [])
        
        validated = {}
        
        for key, prop_schema in properties.items():
            if key not in value:
                if key in required:
                    raise ValueError(f"Required field '{key}' missing in {field_path}")
                continue
            
            validated[key] = SchemaValidator._validate_field(
                value[key], prop_schema, f"{field_path}.{key}"
            )
        
        return validated


def validate_and_sanitize_input(data: Any, schema: Optional[Dict[str, Any]] = None,
                               sanitize: bool = True, level: ValidationLevel = ValidationLevel.NORMAL) -> ValidationResult:
    """
    Validate and sanitize input data.
    
    Args:
        data: Data to validate
        schema: Optional schema for validation
        sanitize: Whether to sanitize the data
        level: Validation level
        
    Returns:
        Validation result
    """
    errors = []
    warnings = []
    sanitized = False
    
    try:
        # Apply schema validation if provided
        if schema:
            data = SchemaValidator.validate_dict_schema(data, schema)
        
        # Sanitize if requested
        if sanitize and isinstance(data, dict):
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = DataSanitizer.sanitize_string(value)
                else:
                    sanitized_data[key] = value
            data = sanitized_data
            sanitized = True
        
        return ValidationResult(
            is_valid=True,
            value=data,
            errors=errors,
            warnings=warnings,
            sanitized=sanitized
        )
        
    except Exception as e:
        errors.append(str(e))
        return ValidationResult(
            is_valid=False,
            value=data,
            errors=errors,
            warnings=warnings,
            sanitized=sanitized
        ) 