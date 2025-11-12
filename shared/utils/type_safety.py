"""
Enhanced type safety system with runtime type checking and validation.
"""

import inspect
import functools
from typing import Any, Dict, List, Optional, Union, TypeVar, Callable, Type, get_type_hints
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TypeCheckMode(Enum):
    """Type checking modes."""
    DISABLED = "disabled"
    WARN = "warn"
    STRICT = "strict"


@dataclass
class TypeCheckResult:
    """Result of type checking."""
    is_valid: bool
    actual_type: type
    expected_type: type
    field_name: str
    message: str


class TypeChecker:
    """Runtime type checker."""
    
    def __init__(self, mode: TypeCheckMode = TypeCheckMode.WARN):
        self.mode = mode
    
    def check_type(self, value: Any, expected_type: type, field_name: str = "value") -> TypeCheckResult:
        """
        Check if value matches expected type.
        
        Args:
            value: Value to check
            expected_type: Expected type
            field_name: Name of the field for error messages
            
        Returns:
            Type check result
        """
        actual_type = type(value)
        is_valid = isinstance(value, expected_type)
        
        if not is_valid:
            message = f"Expected {expected_type.__name__} for {field_name}, got {actual_type.__name__}"
        else:
            message = ""
        
        result = TypeCheckResult(
            is_valid=is_valid,
            actual_type=actual_type,
            expected_type=expected_type,
            field_name=field_name,
            message=message
        )
        
        if not is_valid:
            if self.mode == TypeCheckMode.STRICT:
                raise TypeError(result.message)
            elif self.mode == TypeCheckMode.WARN:
                logger.warning(result.message)
        
        return result
    
    def check_optional_type(self, value: Any, expected_type: type, field_name: str = "value") -> TypeCheckResult:
        """
        Check optional type.
        
        Args:
            value: Value to check
            expected_type: Expected type
            field_name: Name of the field for error messages
            
        Returns:
            Type check result
        """
        if value is None:
            return TypeCheckResult(
                is_valid=True,
                actual_type=type(None),
                expected_type=expected_type,
                field_name=field_name,
                message=""
            )
        
        return self.check_type(value, expected_type, field_name)
    
    def check_union_type(self, value: Any, expected_types: List[type], field_name: str = "value") -> TypeCheckResult:
        """
        Check union type.
        
        Args:
            value: Value to check
            expected_types: List of expected types
            field_name: Name of the field for error messages
            
        Returns:
            Type check result
        """
        actual_type = type(value)
        
        for expected_type in expected_types:
            if isinstance(value, expected_type):
                return TypeCheckResult(
                    is_valid=True,
                    actual_type=actual_type,
                    expected_type=expected_type,
                    field_name=field_name,
                    message=""
                )
        
        type_names = [t.__name__ for t in expected_types]
        message = f"Expected one of {type_names} for {field_name}, got {actual_type.__name__}"
        
        result = TypeCheckResult(
            is_valid=False,
            actual_type=actual_type,
            expected_type=expected_types[0],  # Use first type for display
            field_name=field_name,
            message=message
        )
        
        if self.mode == TypeCheckMode.STRICT:
            raise TypeError(result.message)
        elif self.mode == TypeCheckMode.WARN:
            logger.warning(result.message)
        
        return result


def type_check(mode: TypeCheckMode = TypeCheckMode.WARN):
    """
    Decorator to add runtime type checking to functions.
    
    Args:
        mode: Type checking mode
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get type hints
            type_hints = get_type_hints(func)
            checker = TypeChecker(mode)
            
            # Check arguments
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name, param_value in bound_args.arguments.items():
                if param_name in type_hints:
                    expected_type = type_hints[param_name]
                    
                    # Handle Optional types
                    if hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union:
                        if type(None) in expected_type.__args__:
                            # This is Optional[T]
                            actual_type = expected_type.__args__[0]
                            checker.check_optional_type(param_value, actual_type, param_name)
                        else:
                            # This is Union[T1, T2, ...]
                            checker.check_union_type(param_value, expected_type.__args__, param_name)
                    else:
                        checker.check_type(param_value, expected_type, param_name)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Check return type
            if 'return' in type_hints:
                expected_return_type = type_hints['return']
                checker.check_type(result, expected_return_type, "return")
            
            return result
        
        return wrapper
    return decorator


class TypedDict:
    """Base class for typed dictionaries."""
    
    def __init__(self, **kwargs):
        self._validate_and_set_attributes(kwargs)
    
    def _validate_and_set_attributes(self, data: Dict[str, Any]):
        """Validate and set attributes based on type hints."""
        type_hints = get_type_hints(self.__class__)
        checker = TypeChecker(TypeCheckMode.STRICT)
        
        for field_name, field_type in type_hints.items():
            if field_name in data:
                value = data[field_name]
                
                # Handle Optional types
                if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                    if type(None) in field_type.__args__:
                        actual_type = field_type.__args__[0]
                        checker.check_optional_type(value, actual_type, field_name)
                    else:
                        checker.check_union_type(value, field_type.__args__, field_name)
                else:
                    checker.check_type(value, field_type, field_name)
                
                setattr(self, field_name, value)
            elif hasattr(self, field_name):
                # Field already has a default value
                pass
            else:
                raise ValueError(f"Required field '{field_name}' missing")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypedDict':
        """Create instance from dictionary."""
        return cls(**data)


class TypedList:
    """Type-safe list implementation."""
    
    def __init__(self, item_type: type, items: Optional[List[Any]] = None):
        self.item_type = item_type
        self.checker = TypeChecker(TypeCheckMode.STRICT)
        self._items = []
        
        if items:
            self.extend(items)
    
    def append(self, item: Any):
        """Append item with type checking."""
        self.checker.check_type(item, self.item_type, "list item")
        self._items.append(item)
    
    def extend(self, items: List[Any]):
        """Extend list with type checking."""
        for item in items:
            self.append(item)
    
    def insert(self, index: int, item: Any):
        """Insert item with type checking."""
        self.checker.check_type(item, self.item_type, "list item")
        self._items.insert(index, item)
    
    def __getitem__(self, index):
        return self._items[index]
    
    def __setitem__(self, index, item):
        self.checker.check_type(item, self.item_type, "list item")
        self._items[index] = item
    
    def __len__(self):
        return len(self._items)
    
    def __iter__(self):
        return iter(self._items)
    
    def __contains__(self, item):
        return item in self._items
    
    def to_list(self) -> List[Any]:
        """Convert to regular list."""
        return list(self._items)


class TypedDict:
    """Type-safe dictionary implementation."""
    
    def __init__(self, key_type: type, value_type: type, items: Optional[Dict[Any, Any]] = None):
        self.key_type = key_type
        self.value_type = value_type
        self.checker = TypeChecker(TypeCheckMode.STRICT)
        self._items = {}
        
        if items:
            self.update(items)
    
    def __setitem__(self, key, value):
        """Set item with type checking."""
        self.checker.check_type(key, self.key_type, "dict key")
        self.checker.check_type(value, self.value_type, "dict value")
        self._items[key] = value
    
    def __getitem__(self, key):
        return self._items[key]
    
    def __contains__(self, key):
        return key in self._items
    
    def __len__(self):
        return len(self._items)
    
    def __iter__(self):
        return iter(self._items)
    
    def update(self, other: Dict[Any, Any]):
        """Update with type checking."""
        for key, value in other.items():
            self[key] = value
    
    def to_dict(self) -> Dict[Any, Any]:
        """Convert to regular dictionary."""
        return dict(self._items)


# Type aliases for common use cases - removed problematic ones
# StringList = TypedList[str]
# IntegerList = TypedList[int]
# FloatList = TypedList[float]
# BooleanList = TypedList[bool]

# StringDict = TypedDict[str, str]
# StringAnyDict = TypedDict[str, Any]
# IntegerStringDict = TypedDict[int, str]


def validate_function_signature(func: Callable, *args, **kwargs) -> bool:
    """
    Validate function signature against provided arguments.
    
    Args:
        func: Function to validate
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        True if signature is valid
    """
    try:
        sig = inspect.signature(func)
        sig.bind(*args, **kwargs)
        return True
    except TypeError:
        return False


def get_function_type_info(func: Callable) -> Dict[str, Any]:
    """
    Get detailed type information for a function.
    
    Args:
        func: Function to analyze
        
    Returns:
        Type information dictionary
    """
    type_hints = get_type_hints(func)
    sig = inspect.signature(func)
    
    return {
        "name": func.__name__,
        "module": func.__module__,
        "type_hints": type_hints,
        "parameters": {
            name: {
                "type": type_hints.get(name, "Any"),
                "default": param.default if param.default is not inspect.Parameter.empty else None,
                "kind": str(param.kind)
            }
            for name, param in sig.parameters.items()
        },
        "return_type": type_hints.get("return", "Any")
    }


def create_type_safe_wrapper(func: Callable, mode: TypeCheckMode = TypeCheckMode.STRICT) -> Callable:
    """
    Create a type-safe wrapper around a function.
    
    Args:
        func: Function to wrap
        mode: Type checking mode
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        checker = TypeChecker(mode)
        type_hints = get_type_hints(func)
        sig = inspect.signature(func)
        
        # Bind arguments
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Check input types
        for param_name, param_value in bound_args.arguments.items():
            if param_name in type_hints:
                expected_type = type_hints[param_name]
                checker.check_type(param_value, expected_type, param_name)
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Check return type
        if 'return' in type_hints:
            checker.check_type(result, type_hints['return'], "return")
        
        return result
    
    return wrapper 