"""
Dependency injection container for managing service dependencies.
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional
from core.config.adapter import get_configuration_manager
from rag.llm.client import LLMClient
from rag.retriever import MultiVectorRetriever
from rag.memory.base import MemoryStrategy, MemoryFactory
from rag.resilience.circuit_breaker import CircuitBreaker
from rag.resilience.retry_handler import RetryHandler

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Container:
    """
    Dependency injection container for managing service dependencies.
    
    This container provides a centralized way to manage service instances,
    reducing coupling between components and enabling easier testing.
    """

    def __init__(self):
        """Initialize the container."""
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._config_manager = get_configuration_manager()

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register a singleton service.
        
        Args:
            interface: Service interface type
            implementation: Service implementation type
        """
        self._singletons[interface] = implementation
        logger.debug(f"Registered singleton: {interface.__name__} -> {implementation.__name__}")

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register a transient service.
        
        Args:
            interface: Service interface type
            implementation: Service implementation type
        """
        self._services[interface] = implementation
        logger.debug(f"Registered transient: {interface.__name__} -> {implementation.__name__}")

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service from the container.
        
        Args:
            interface: Service interface type
            
        Returns:
            Service instance
            
        Raises:
            Exception: If service is not registered
        """
        if interface in self._singletons:
            if interface not in self._services:
                self._services[interface] = self._singletons[interface]()
            return self._services[interface]
        
        if interface in self._services:
            return self._services[interface]()
        
        raise Exception(f"Service {interface} not registered")

    def configure_services(self) -> None:
        """Configure all services with default implementations."""
        logger.info("Configuring services in container")
        
        # Get configuration
        llm_config = self._config_manager.get_llm_config()
        db_config = self._config_manager.get_database_config()
        memory_config = self._config_manager.get_memory_config()
        resilience_config = self._config_manager.get_resilience_config()
        
        # Register LLM client
        self.register_singleton(
            LLMClient, 
            lambda: LLMClient(
                primary_api_key=llm_config.primary_api_key,
                primary_model=llm_config.primary_model,
                fallback_api_key=llm_config.fallback_api_key,
                fallback_model=llm_config.fallback_model,
                enable_circuit_breaker=resilience_config.circuit_breaker_enabled,
                enable_retry=resilience_config.retry_enabled,
            )
        )
        
        # Register retriever
        self.register_singleton(
            MultiVectorRetriever,
            lambda: MultiVectorRetriever(
                qdrant_url=db_config.url,
                qdrant_api_key=db_config.api_key,
                embedding_model=self._config_manager.get_str("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            )
        )
        
        # Register memory strategy
        memory_type = memory_config.memory_type
        
        # Auto-select Redis if enabled, regardless of memory_type setting
        if self._config_manager.get_bool("REDIS_ENABLED", False):
            self.register_singleton(
                MemoryStrategy,
                lambda: MemoryFactory.create_memory(
                    memory_type="redis",
                    max_entries=self._config_manager.get_int("REDIS_MAX_ENTRIES", 100),
                    max_age_hours=self._config_manager.get_int("REDIS_TTL_HOURS", 24),
                )
            )
            logger.info("Auto-selected Redis memory backend (REDIS_ENABLED=true)")
        elif memory_type == "redis":
            self.register_singleton(
                MemoryStrategy,
                lambda: MemoryFactory.create_memory(
                    memory_type="redis",
                    max_entries=self._config_manager.get_int("REDIS_MAX_ENTRIES", 100),
                    max_age_hours=self._config_manager.get_int("REDIS_TTL_HOURS", 24),
                )
            )
        elif memory_type == "langchain":
            self.register_singleton(
                MemoryStrategy,
                lambda: MemoryFactory.create_memory(
                    memory_type="langchain",
                    max_entries=memory_config.max_entries,
                    max_age_hours=memory_config.max_age_hours,
                )
            )
        else:
            # Default to in_memory instead of conversation
            self.register_singleton(
                MemoryStrategy,
                lambda: MemoryFactory.create_memory(
                    memory_type="in_memory",
                    max_entries=memory_config.max_entries,
                    max_age_hours=memory_config.max_age_hours,
                )
            )
        
        # Register configuration manager
        self.register_singleton(
            type(self._config_manager),
            lambda: self._config_manager
        )
        
        # Register resilience components
        self.register_singleton(
            CircuitBreaker,
            lambda: CircuitBreaker(
                failure_threshold=resilience_config.failure_threshold,
                recovery_timeout=resilience_config.recovery_timeout,
            )
        )
        
        self.register_singleton(
            RetryHandler,
            lambda: RetryHandler(
                max_retries=resilience_config.max_retries,
                base_delay=resilience_config.base_delay,
                max_delay=resilience_config.max_delay,
            )
        )
        
        # Register RAG service
        try:
            from app.services.rag_service import RAGService
            self.register_singleton(
                RAGService,
                lambda: RAGService()
            )
        except ImportError:
            try:
                from services.rag_service import RAGService
                self.register_singleton(
                    RAGService,
                    lambda: RAGService()
                )
            except ImportError:
                logger.warning("RAGService not available for registration")
        
        logger.info("Services configured successfully")

    def _get_memory_type(self) -> str:
        """Get memory type from configuration."""
        return self._config_manager.get_str("MEMORY_TYPE", "conversation")

    def get_config(self):
        """Get configuration manager."""
        return self._config_manager

    def reset(self) -> None:
        """Reset the container."""
        self._services.clear()
        logger.info("Container reset")

    def get_registered_services(self) -> Dict[str, Any]:
        """Get list of registered services."""
        services = {}
        
        # Add singletons
        for interface, implementation in self._singletons.items():
            services[interface.__name__] = {
                "type": "singleton",
                "implementation": implementation.__name__ if hasattr(implementation, '__name__') else str(implementation)
            }
        
        # Add transients
        for interface, implementation in self._services.items():
            if interface not in self._singletons:
                services[interface.__name__] = {
                    "type": "transient",
                    "implementation": implementation.__name__ if hasattr(implementation, '__name__') else str(implementation)
                }
        
        return services


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        Container instance
    """
    global _container
    if _container is None:
        _container = Container()
        _container.configure_services()
    return _container


def reset_container() -> None:
    """Reset the global container."""
    global _container
    if _container is not None:
        _container.reset()
        _container = None


def register_service(interface: Type[T], implementation: Type[T], singleton: bool = True) -> None:
    """
    Register a service in the global container.
    
    Args:
        interface: Service interface type
        implementation: Service implementation type
        singleton: Whether to register as singleton
    """
    container = get_container()
    if singleton:
        container.register_singleton(interface, implementation)
    else:
        container.register_transient(interface, implementation)


def resolve_service(interface: Type[T]) -> T:
    """
    Resolve a service from the global container.
    
    Args:
        interface: Service interface type
        
    Returns:
        Service instance
    """
    container = get_container()
    return container.resolve(interface) 