"""
Base memory interface for conversation memory implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryStrategy(ABC):
    """
    Abstract base class for memory implementations.
    
    This defines the contract that all memory implementations must follow,
    enabling easy swapping between different memory backends.
    """

    @abstractmethod
    def add_interaction(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an interaction to memory.
        
        Args:
            session_id: Unique session identifier
            question: User question
            answer: AI response
            context: Retrieved context used for response
            metadata: Additional metadata for the interaction
        """
        pass

    @abstractmethod
    async def add_interaction_async(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an interaction to memory asynchronously.
        
        Args:
            session_id: Unique session identifier
            question: User question
            answer: AI response
            context: Retrieved context used for response
            metadata: Additional metadata for the interaction
        """
        pass

    @abstractmethod
    def get_recent_context(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation context for a session.
        
        Args:
            session_id: Unique session identifier
            max_entries: Maximum number of recent interactions to return
            
        Returns:
            List of recent interactions with metadata
        """
        pass

    @abstractmethod
    async def get_recent_context_async(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation context for a session asynchronously.
        
        Args:
            session_id: Unique session identifier
            max_entries: Maximum number of recent interactions to return
            
        Returns:
            List of recent interactions with metadata
        """
        pass

    @abstractmethod
    def get_conversation_summary(self, session_id: str) -> str:
        """
        Get a summary of the conversation for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Summary of the conversation
        """
        pass

    @abstractmethod
    async def get_conversation_summary_async(self, session_id: str) -> str:
        """
        Get a summary of the conversation for a session asynchronously.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Summary of the conversation
        """
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """
        Clear all memory for a specific session.
        
        Args:
            session_id: Unique session identifier
        """
        pass

    @abstractmethod
    async def clear_session_async(self, session_id: str) -> None:
        """
        Clear all memory for a specific session asynchronously.
        
        Args:
            session_id: Unique session identifier
        """
        pass

    @abstractmethod
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        pass

    @abstractmethod
    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """
        Get memory statistics asynchronously.
        
        Returns:
            Dictionary with memory statistics
        """
        pass


class MemoryFactory:
    """
    Factory for creating memory implementations.
    """
    
    @staticmethod
    def create_memory(memory_type: str, **kwargs) -> MemoryStrategy:
        """
        Create a memory implementation based on type.
        
        Args:
            memory_type: Type of memory to create ('in_memory', 'redis', 'langchain')
            **kwargs: Additional arguments for memory initialization
            
        Returns:
            Memory strategy instance
            
        Raises:
            ValueError: If memory_type is not supported
        """
        if memory_type == "in_memory":
            from rag.memory.conversation import ConversationMemory
            return ConversationMemory(**kwargs)
        elif memory_type == "redis":
            from rag.memory.redis_memory import RedisConversationMemory
            return RedisConversationMemory(**kwargs)
        elif memory_type == "langchain":
            from rag.memory.langchain_memory import LangChainConversationMemory
            return LangChainConversationMemory(**kwargs)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}") 