"""
Configuration adapter that wraps the existing Config class.
"""

from typing import Any, Dict, Optional
from core.config.interface import IConfigurationProvider
# Handle imports for different execution contexts
try:
    # Try importing as if running from root directory
    from app.config import Config
except ImportError:
    # Try importing as if running from app directory
    try:
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
        
        from config import Config


class ConfigAdapter(IConfigurationProvider):
    """
    Adapter that wraps the existing Config class to implement the interface.
    """
    
    def __init__(self):
        self._config = Config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            return getattr(self._config, key, default)
        except AttributeError:
            return default
    
    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value."""
        value = self.get(key, default)
        if value is None:
            return default
        value_str = str(value)
        # Return None for empty strings or "None" strings to allow proper fallback handling
        if value_str.strip() == "" or value_str.lower() == "none":
            return None
        return value_str
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(key, default)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(value, (int, float)):
            return bool(value)
        return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        value = self.get(key, default)
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def validate_required_configs(self) -> bool:
        """Validate required configuration values."""
        try:
            self._config.validate_required_configs()
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        try:
            return self._config.to_dict()
        except Exception:
            return {}


def get_configuration_manager() -> 'ConfigurationManager':
    """
    Get configuration manager instance.
    
    Returns:
        ConfigurationManager instance
    """
    from core.config.interface import ConfigurationManager
    adapter = ConfigAdapter()
    return ConfigurationManager(adapter) 