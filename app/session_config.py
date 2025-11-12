import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SessionConfig:
    """Configuration for session management"""

    # Session limits
    MAX_MESSAGES: int = 50
    MAX_SESSION_AGE_HOURS: int = 24
    MAX_CONTEXT_SIZE: int = 10000  # 10KB

    # Cleanup settings
    CLEANUP_INTERVAL_MINUTES: int = 30
    AUTO_CLEANUP: bool = True

    # Persistence settings
    ENABLE_PERSISTENCE: bool = True
    ENABLE_COMPRESSION: bool = True
    PERSISTENCE_KEY: str = "session_data"

    # Memory management
    MAX_DEBUG_DATA_SIZE: int = 5000  # 5KB
    MAX_METADATA_SIZE: int = 2000  # 2KB

    # Performance settings
    ENABLE_SESSION_ANALYTICS: bool = True
    ENABLE_HEALTH_MONITORING: bool = True
    ENABLE_ERROR_RECOVERY: bool = True

    # Security settings
    SANITIZE_SESSION_DATA: bool = True
    REMOVE_SENSITIVE_DATA: bool = True

    @classmethod
    def from_env(cls) -> "SessionConfig":
        """Create config from environment variables"""
        return cls(
            MAX_MESSAGES=int(os.getenv("SESSION_MAX_MESSAGES", "50")),
            MAX_SESSION_AGE_HOURS=int(os.getenv("SESSION_MAX_AGE_HOURS", "24")),
            MAX_CONTEXT_SIZE=int(os.getenv("SESSION_MAX_CONTEXT_SIZE", "10000")),
            CLEANUP_INTERVAL_MINUTES=int(os.getenv("SESSION_CLEANUP_INTERVAL", "30")),
            AUTO_CLEANUP=os.getenv("SESSION_AUTO_CLEANUP", "true").lower() == "true",
            ENABLE_PERSISTENCE=os.getenv("SESSION_ENABLE_PERSISTENCE", "true").lower()
            == "true",
            ENABLE_COMPRESSION=os.getenv("SESSION_ENABLE_COMPRESSION", "true").lower()
            == "true",
            PERSISTENCE_KEY=os.getenv("SESSION_PERSISTENCE_KEY", "session_data"),
            MAX_DEBUG_DATA_SIZE=int(os.getenv("SESSION_MAX_DEBUG_SIZE", "5000")),
            MAX_METADATA_SIZE=int(os.getenv("SESSION_MAX_METADATA_SIZE", "2000")),
            ENABLE_SESSION_ANALYTICS=os.getenv(
                "SESSION_ENABLE_ANALYTICS", "true"
            ).lower()
            == "true",
            ENABLE_HEALTH_MONITORING=os.getenv(
                "SESSION_ENABLE_HEALTH_MONITORING", "true"
            ).lower()
            == "true",
            ENABLE_ERROR_RECOVERY=os.getenv(
                "SESSION_ENABLE_ERROR_RECOVERY", "true"
            ).lower()
            == "true",
            SANITIZE_SESSION_DATA=os.getenv("SESSION_SANITIZE_DATA", "true").lower()
            == "true",
            REMOVE_SENSITIVE_DATA=os.getenv("SESSION_REMOVE_SENSITIVE", "true").lower()
            == "true",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "MAX_MESSAGES": self.MAX_MESSAGES,
            "MAX_SESSION_AGE_HOURS": self.MAX_SESSION_AGE_HOURS,
            "MAX_CONTEXT_SIZE": self.MAX_CONTEXT_SIZE,
            "CLEANUP_INTERVAL_MINUTES": self.CLEANUP_INTERVAL_MINUTES,
            "AUTO_CLEANUP": self.AUTO_CLEANUP,
            "ENABLE_PERSISTENCE": self.ENABLE_PERSISTENCE,
            "ENABLE_COMPRESSION": self.ENABLE_COMPRESSION,
            "PERSISTENCE_KEY": self.PERSISTENCE_KEY,
            "MAX_DEBUG_DATA_SIZE": self.MAX_DEBUG_DATA_SIZE,
            "MAX_METADATA_SIZE": self.MAX_METADATA_SIZE,
            "ENABLE_SESSION_ANALYTICS": self.ENABLE_SESSION_ANALYTICS,
            "ENABLE_HEALTH_MONITORING": self.ENABLE_HEALTH_MONITORING,
            "ENABLE_ERROR_RECOVERY": self.ENABLE_ERROR_RECOVERY,
            "SANITIZE_SESSION_DATA": self.SANITIZE_SESSION_DATA,
            "REMOVE_SENSITIVE_DATA": self.REMOVE_SENSITIVE_DATA,
        }


# Default configuration
DEFAULT_SESSION_CONFIG = SessionConfig()

# Environment-specific configurations
PRODUCTION_SESSION_CONFIG = SessionConfig(
    MAX_MESSAGES=30,  # Lower limit for production
    MAX_SESSION_AGE_HOURS=12,  # Shorter sessions
    CLEANUP_INTERVAL_MINUTES=15,  # More frequent cleanup
    ENABLE_HEALTH_MONITORING=True,
    ENABLE_ERROR_RECOVERY=True,
    SANITIZE_SESSION_DATA=True,
)

DEVELOPMENT_SESSION_CONFIG = SessionConfig(
    MAX_MESSAGES=100,  # Higher limit for development
    MAX_SESSION_AGE_HOURS=48,  # Longer sessions
    CLEANUP_INTERVAL_MINUTES=60,  # Less frequent cleanup
    ENABLE_HEALTH_MONITORING=True,
    ENABLE_ERROR_RECOVERY=True,
    SANITIZE_SESSION_DATA=False,  # Keep all data for debugging
)


def get_session_config(environment: str = None) -> SessionConfig:
    """Get session configuration for the specified environment"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")

    configs = {
        "production": PRODUCTION_SESSION_CONFIG,
        "development": DEVELOPMENT_SESSION_CONFIG,
        "default": DEFAULT_SESSION_CONFIG,
    }

    return configs.get(environment.lower(), DEFAULT_SESSION_CONFIG)
