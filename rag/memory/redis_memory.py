"""
Redis memory implementation for conversation management.
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from app.config import Config
from rag.memory.base import MemoryStrategy

logger = logging.getLogger(__name__)


class RedisConversationMemory(MemoryStrategy):
    """
    Redis-based conversation memory implementation.
    
    This implementation uses Redis for distributed conversation
    memory management across multiple instances.
    """

    def __init__(self, max_entries: int = Config.MEMORY_MAX_ENTRIES, max_age_hours: int = Config.MEMORY_MAX_AGE_HOURS):
        """Initialize Redis conversation memory."""
        self.max_entries = max_entries
        self.max_age_hours = max_age_hours
        self.redis_client = None
        self._initialize_redis()
        logger.info(f"RedisConversationMemory initialized with max_entries={max_entries}, max_age_hours={max_age_hours}")

    def _initialize_redis(self):
        """Initialize Redis client."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to in-memory storage.")
            self.redis_client = None

    def add_interaction(
        self, 
        session_id: str, 
        question: str, 
        answer: str, 
        context: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an interaction to memory."""
        logger.info(f"RedisConversationMemory.add_interaction called for session: {session_id}")
        
        if not self.redis_client:
            logger.warning("Redis not available, skipping interaction storage")
            return
        
        try:
            interaction = {
                "question": question,
                "answer": answer,
                "context": context,
                "metadata": metadata or {},
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Get existing interactions
            key = f"conversation:{session_id}"
            existing_data = self.redis_client.get(key)
            
            if existing_data:
                interactions = json.loads(existing_data)
            else:
                interactions = []
            
            # Add new interaction
            interactions.append(interaction)
            
            # Maintain max entries limit
            if len(interactions) > self.max_entries:
                interactions = interactions[-self.max_entries:]
            
            # Store back to Redis
            self.redis_client.setex(
                key, 
                self.max_age_hours * 3600,  # TTL in seconds
                json.dumps(interactions)
            )
            
            logger.info(f"Added interaction to Redis. Session {session_id} now has {len(interactions)} interactions")
            
        except Exception as e:
            logger.error(f"Error adding interaction to Redis: {e}")

    async def add_interaction_async(
        self, 
        session_id: str, 
        question: str, 
        answer: str, 
        context: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an interaction to memory asynchronously."""
        self.add_interaction(session_id, question, answer, context, metadata)
        logger.info(f"Added interaction to Redis for session {session_id}")

    def get_recent_context(self, session_id: str, max_entries: int = None) -> List[Dict[str, Any]]:
        """Get recent conversation context."""
        logger.info(f"RedisConversationMemory.get_recent_context called for session: {session_id}, max_entries: {max_entries}")
        
        if not self.redis_client:
            logger.warning("Redis not available, returning empty context")
            return []
        
        try:
            key = f"conversation:{session_id}"
            data = self.redis_client.get(key)
            
            if not data:
                logger.info(f"No conversation history found for session: {session_id}")
                return []
            
            interactions = json.loads(data)
            logger.info(f"Found {len(interactions)} recent interactions for session: {session_id}")
            
            # Filter expired entries
            current_time = asyncio.get_event_loop().time()
            valid_entries = [
                entry for entry in interactions
                if current_time - entry["timestamp"] < (self.max_age_hours * 3600)
            ]
            
            logger.info(f"After filtering expired entries: {len(valid_entries)} valid interactions")
            
            if max_entries:
                valid_entries = valid_entries[-max_entries:]
            
            return valid_entries
            
        except Exception as e:
            logger.error(f"Error getting context from Redis: {e}")
            return []

    async def get_recent_context_async(self, session_id: str, max_entries: int = None) -> List[Dict[str, Any]]:
        """Get recent conversation context asynchronously."""
        return self.get_recent_context(session_id, max_entries)

    def clear_session(self, session_id: str) -> None:
        """Clear memory for a specific session."""
        if not self.redis_client:
            logger.warning("Redis not available, cannot clear session")
            return
        
        try:
            key = f"conversation:{session_id}"
            self.redis_client.delete(key)
            logger.info(f"Cleared memory for session: {session_id}")
        except Exception as e:
            logger.error(f"Error clearing session from Redis: {e}")

    async def clear_session_async(self, session_id: str) -> None:
        """Clear memory for a specific session asynchronously."""
        self.clear_session(session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.redis_client:
            return {
                "memory_type": "redis",
                "status": "unavailable",
                "error": "Redis connection not available"
            }
        
        try:
            # Get all conversation keys
            keys = self.redis_client.keys("conversation:*")
            total_sessions = len(keys)
            
            total_interactions = 0
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    interactions = json.loads(data)
                    total_interactions += len(interactions)
            
            return {
                "memory_type": "redis",
                "status": "available",
                "total_sessions": total_sessions,
                "total_interactions": total_interactions,
                "max_entries": self.max_entries,
                "max_age_hours": self.max_age_hours,
                "redis_keys": keys
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis memory stats: {e}")
            return {
                "memory_type": "redis",
                "status": "error",
                "error": str(e)
            }

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory statistics asynchronously."""
        return self.get_memory_stats()

    def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation for a session."""
        interactions = self.get_recent_context(session_id, max_entries=5)
        
        if not interactions:
            return ""
        
        summary_parts = []
        for interaction in interactions:
            summary_parts.append(f"Q: {interaction['question']}")
            summary_parts.append(f"A: {interaction['answer']}")
        
        return "\n".join(summary_parts)

    async def get_conversation_summary_async(self, session_id: str) -> str:
        """Get a summary of the conversation for a session asynchronously."""
        return self.get_conversation_summary(session_id) 