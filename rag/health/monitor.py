"""
Health monitoring and system status utilities.
"""

import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class HealthMonitor(ABC):
    """
    Abstract base class for health monitoring.
    """
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status."""
        pass
    
    @abstractmethod
    async def get_health_status_async(self) -> Dict[str, Any]:
        """Get health status asynchronously."""
        pass


class SystemHealthMonitor(HealthMonitor):
    """
    System health monitoring implementation.
    """
    
    def __init__(self, memory, memory_enabled: bool, model: str, retriever, llm_client):
        self.memory = memory
        self.memory_enabled = memory_enabled
        self.model = model
        self.retriever = retriever
        self.llm_client = llm_client
        self.start_time = time.time()
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status.
        
        Returns:
            Dictionary containing health status information
        """
        try:
            # Memory health
            memory_stats = {}
            if self.memory_enabled and self.memory:
                try:
                    memory_stats = self.memory.get_memory_stats()
                except Exception as e:
                    logger.warning(f"Error getting memory stats: {e}")
                    memory_stats = {"error": str(e)}
            
            # LLM health
            llm_health = {}
            if self.llm_client:
                try:
                    llm_health = self.llm_client.get_health_status()
                except Exception as e:
                    logger.warning(f"Error getting LLM health: {e}")
                    llm_health = {"error": str(e)}
            
            # Retriever health
            retriever_health = {}
            if self.retriever:
                try:
                    retriever_health = self.retriever.get_collection_info()
                except Exception as e:
                    logger.warning(f"Error getting retriever health: {e}")
                    retriever_health = {"error": str(e)}
            
            # System uptime
            uptime = time.time() - self.start_time
            
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                "memory": {
                    "enabled": self.memory_enabled,
                    "stats": memory_stats
                },
                "llm": {
                    "model": self.model,
                    "health": llm_health
                },
                "retriever": {
                    "health": retriever_health
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_health_status_async(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status asynchronously.
        
        Returns:
            Dictionary containing health status information
        """
        try:
            # Memory health
            memory_stats = {}
            if self.memory_enabled and self.memory:
                try:
                    memory_stats = await self.memory.get_memory_stats_async()
                except Exception as e:
                    logger.warning(f"Error getting memory stats: {e}")
                    memory_stats = {"error": str(e)}
            
            # LLM health
            llm_health = {}
            if self.llm_client:
                try:
                    llm_health = await self.llm_client.get_health_status_async()
                except Exception as e:
                    logger.warning(f"Error getting LLM health: {e}")
                    llm_health = {"error": str(e)}
            
            # Retriever health
            retriever_health = {}
            if self.retriever:
                try:
                    retriever_health = self.retriever.get_collection_info()
                except Exception as e:
                    logger.warning(f"Error getting retriever health: {e}")
                    retriever_health = {"error": str(e)}
            
            # System uptime
            uptime = time.time() - self.start_time
            
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                "memory": {
                    "enabled": self.memory_enabled,
                    "stats": memory_stats
                },
                "llm": {
                    "model": self.model,
                    "health": llm_health
                },
                "retriever": {
                    "health": retriever_health
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in async health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


def get_system_health_sync(memory, memory_enabled: bool, model: str, retriever, llm_client) -> Dict[str, Any]:
    """
    Get system health status synchronously.
    
    Args:
        memory: Memory instance
        memory_enabled: Whether memory is enabled
        model: Model name
        retriever: Retriever instance
        llm_client: LLM client instance
        
    Returns:
        Health status dictionary
    """
    monitor = SystemHealthMonitor(memory, memory_enabled, model, retriever, llm_client)
    return monitor.get_health_status()


async def get_system_health_async(memory, memory_enabled: bool, model: str, retriever, llm_client) -> Dict[str, Any]:
    """
    Get system health status asynchronously.
    
    Args:
        memory: Memory instance
        memory_enabled: Whether memory is enabled
        model: Model name
        retriever: Retriever instance
        llm_client: LLM client instance
        
    Returns:
        Health status dictionary
    """
    monitor = SystemHealthMonitor(memory, memory_enabled, model, retriever, llm_client)
    return await monitor.get_health_status_async() 