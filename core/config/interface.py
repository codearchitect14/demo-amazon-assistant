"""
Configuration interface and abstraction layer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


class IConfigurationProvider(ABC):
    """
    Abstract interface for configuration providers.
    """
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value."""
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        pass
    
    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        pass
    
    @abstractmethod
    def validate_required_configs(self) -> bool:
        """Validate required configuration values."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        pass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    api_key: Optional[str] = None
    timeout: int = 30


@dataclass
class LLMConfig:
    """LLM configuration."""
    primary_api_key: str
    primary_model: str
    fallback_api_key: Optional[str] = None
    fallback_model: Optional[str] = None
    timeout: int = 60


@dataclass
class MemoryConfig:
    """Memory configuration."""
    enabled: bool = True
    max_entries: int = 100
    max_age_hours: int = 24
    memory_type: str = "conversation"


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    ttl: int = 3600
    max_size: int = 1000


@dataclass
class ResilienceConfig:
    """Resilience configuration."""
    circuit_breaker_enabled: bool = True
    retry_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0


class ConfigurationManager:
    """
    Configuration manager that abstracts configuration access.
    """
    
    def __init__(self, provider: IConfigurationProvider):
        self._provider = provider
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._provider.get(key, default)
    
    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value."""
        return self._provider.get_str(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        return self._provider.get_int(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        return self._provider.get_bool(key, default)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        return self._provider.get_float(key, default)
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(
            url=self.get_str("QDRANT_URL", "http://localhost:6333"),
            api_key=self.get_str("QDRANT_API_KEY"),
            timeout=self.get_int("DB_TIMEOUT", 30)
        )
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return LLMConfig(
            primary_api_key=self.get_str("GROQ_API_KEY"),
            primary_model=self.get_str("GROQ_PRIMARY_MODEL", "llama-3.3-70b-versatile"),
            fallback_api_key=self.get_str("GROQ_FALLBACK_API_KEY"),
            fallback_model=self.get_str("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant"),
            timeout=self.get_int("LLM_TIMEOUT", 60)
        )
    
    def get_memory_config(self) -> MemoryConfig:
        """Get memory configuration."""
        return MemoryConfig(
            enabled=self.get_bool("MEMORY_ENABLED", True),
            max_entries=self.get_int("MEMORY_MAX_ENTRIES", 100),
            max_age_hours=self.get_int("MEMORY_MAX_AGE_HOURS", 24),
            memory_type=self.get_str("MEMORY_TYPE", "conversation")
        )
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        return CacheConfig(
            enabled=self.get_bool("CACHE_ENABLED", True),
            ttl=self.get_int("CACHE_TTL", 3600),
            max_size=self.get_int("CACHE_MAX_SIZE", 1000)
        )
    
    def get_resilience_config(self) -> ResilienceConfig:
        """Get resilience configuration."""
        return ResilienceConfig(
            circuit_breaker_enabled=self.get_bool("ENABLE_CIRCUIT_BREAKER", True),
            retry_enabled=self.get_bool("ENABLE_RETRY_LOGIC", True),
            failure_threshold=self.get_int("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5),
            recovery_timeout=self.get_int("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 60),
            max_retries=self.get_int("RETRY_MAX_RETRIES", 3),
            base_delay=self.get_float("RETRY_BASE_DELAY", 1.0),
            max_delay=self.get_float("RETRY_MAX_DELAY", 60.0)
        )
    
    def validate_required_configs(self) -> bool:
        """Validate required configuration values."""
        return self._provider.validate_required_configs()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self._provider.to_dict() 