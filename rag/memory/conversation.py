"""
In-memory conversation memory implementation with rich logging.
"""

import time
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from app.config import Config
from rag.memory.base import MemoryStrategy
from rich_logging import log_memory_operation, count_tokens

logger = logging.getLogger(__name__)


class ConversationMemory(MemoryStrategy):
    """
    Simple in-memory conversation history manager with rich logging.
    
    This implementation stores conversation history in memory and is suitable
    for single-instance deployments or development environments.
    """

    def __init__(
        self,
        max_entries: int = Config.MEMORY_MAX_ENTRIES,
        max_age_hours: int = Config.MEMORY_MAX_AGE_HOURS,
    ):
        """
        Initialize conversation memory.
        
        Args:
            max_entries: Maximum number of entries per session
            max_age_hours: Maximum age of entries in hours
        """
        self.max_entries = max_entries
        self.max_age_seconds = max_age_hours * 3600
        self.conversations = {}  # session_id -> conversation_history
        
        # Structured logging for initialization
        logger.info("ConversationMemory initialized", extra={
            "component": "memory",
            "memory_type": "in_memory",
            "max_entries": max_entries,
            "max_age_hours": max_age_hours,
            "optimization": "context_removed",
            "note": "full_answers_stored"
        })

    def add_interaction(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a new interaction to the conversation memory.
        
        Args:
            session_id: Unique session identifier
            question: User question
            answer: AI response
            context: Retrieved context used for response (not stored in memory)
            metadata: Additional metadata for the interaction
        """
        start_time = time.time()
        
        # Log the operation start
        logger.info("Adding interaction to conversation memory", extra={
            "component": "memory",
            "operation": "add_interaction",
            "session_id": session_id,
            "question_length": len(question),
            "answer_length": len(answer),
            "context_length": len(context),
            "has_metadata": metadata is not None,
            "optimization": "context_not_stored"
        })

        if not Config.MEMORY_ENABLED:
            logger.warning("Memory not enabled in config", extra={
                "component": "memory",
                "operation": "add_interaction",
                "session_id": session_id,
                "status": "skipped"
            })
            return

        if session_id not in self.conversations:
            logger.info("Creating new conversation list for session", extra={
                "component": "memory",
                "operation": "create_session",
                "session_id": session_id,
                "total_sessions": len(self.conversations) + 1
            })
            self.conversations[session_id] = []

        # Only store essential conversation data - not the context
        interaction = {
            "timestamp": time.time(),
            "question": question,
            "answer": answer,  # Full answer stored (no truncation)
            "metadata": metadata or {},
            # Note: context is not stored to save memory and reduce token usage
        }

        self.conversations[session_id].append(interaction)
        
        # Calculate memory usage metrics
        interaction_size = len(json.dumps(interaction))
        session_size = len(json.dumps(self.conversations[session_id]))
        total_interactions = len(self.conversations[session_id])
        
        # Calculate token savings from context optimization
        context_tokens = count_tokens(context) if context else 0
        
        # Log with rich logging
        log_memory_operation("Add Interaction", session_id, {
            "interaction_size_bytes": interaction_size,
            "session_size_bytes": session_size,
            "total_interactions": total_interactions,
            "context_saved_bytes": len(context),
            "context_saved_tokens": context_tokens,
            "processing_time_ms": (time.time() - start_time) * 1000
        })
        
        # Log successful addition with metrics
        logger.info("Successfully added interaction to memory", extra={
            "component": "memory",
            "operation": "add_interaction",
            "session_id": session_id,
            "interaction_size_bytes": interaction_size,
            "session_size_bytes": session_size,
            "total_interactions": total_interactions,
            "context_optimization": "enabled",
            "context_saved_bytes": len(context),
            "context_saved_tokens": context_tokens,
            "processing_time_ms": (time.time() - start_time) * 1000
        })

        # Clean up old entries
        self._cleanup_old_entries(session_id)

    async def add_interaction_async(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a new interaction to the conversation memory asynchronously.
        
        Args:
            session_id: Unique session identifier
            question: User question
            answer: AI response
            context: Retrieved context used for response (not stored in memory)
            metadata: Additional metadata for the interaction
        """
        logger.info("Adding interaction to conversation memory (async)", extra={
            "component": "memory",
            "operation": "add_interaction_async",
            "session_id": session_id,
            "question_length": len(question),
            "answer_length": len(answer),
            "context_length": len(context)
        })
        return await asyncio.to_thread(
            self.add_interaction, session_id, question, answer, context, metadata
        )

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
        start_time = time.time()
        
        logger.info("Getting recent conversation context", extra={
            "component": "memory",
            "operation": "get_recent_context",
            "session_id": session_id,
            "max_entries": max_entries
        })
        
        if not Config.MEMORY_ENABLED or session_id not in self.conversations:
            logger.info("Memory not enabled or session not found", extra={
                "component": "memory",
                "operation": "get_recent_context",
                "session_id": session_id,
                "memory_enabled": Config.MEMORY_ENABLED,
                "session_exists": session_id in self.conversations,
                "result": "empty_list"
            })
            return []

        # Get recent entries, excluding the current interaction
        recent = self.conversations[session_id][-max_entries:]
        
        # Filter out expired entries
        current_time = time.time()
        valid_entries = [
            entry
            for entry in recent
            if current_time - entry["timestamp"] < self.max_age_seconds
        ]

        # Calculate metrics
        total_entries = len(self.conversations[session_id])
        expired_entries = len(recent) - len(valid_entries)
        context_size = len(json.dumps(valid_entries))
        
        # Calculate token usage for retrieved history
        history_text = ""
        for entry in valid_entries:
            history_text += f"Q: {entry['question']}\nA: {entry['answer']}\n\n"
        
        history_tokens = count_tokens(history_text)
        
        logger.info("Retrieved recent conversation context", extra={
            "component": "memory",
            "operation": "get_recent_context",
            "session_id": session_id,
            "total_entries_in_session": total_entries,
            "requested_entries": max_entries,
            "valid_entries_returned": len(valid_entries),
            "expired_entries_filtered": expired_entries,
            "context_size_bytes": context_size,
            "history_tokens": history_tokens,
            "processing_time_ms": (time.time() - start_time) * 1000
        })
        
        return valid_entries

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
        logger.info("Getting recent conversation context (async)", extra={
            "component": "memory",
            "operation": "get_recent_context_async",
            "session_id": session_id,
            "max_entries": max_entries
        })
        return await asyncio.to_thread(self.get_recent_context, session_id, max_entries)

    def get_conversation_summary(self, session_id: str) -> str:
        """
        Get a summary of the conversation history.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Summary of the conversation
        """
        start_time = time.time()
        
        logger.info("Generating conversation summary", extra={
            "component": "memory",
            "operation": "get_conversation_summary",
            "session_id": session_id
        })
        
        if not Config.MEMORY_ENABLED or session_id not in self.conversations:
            logger.info("Memory not enabled or session not found for summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "session_id": session_id,
                "memory_enabled": Config.MEMORY_ENABLED,
                "session_exists": session_id in self.conversations,
                "result": "empty_summary"
            })
            return ""

        recent_context = self.get_recent_context(session_id, max_entries=5)
        
        if not recent_context:
            logger.info("No recent context found for summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "session_id": session_id,
                "result": "empty_summary"
            })
            return ""

        summary_parts = ["Previous conversation context:"]

        for i, entry in enumerate(recent_context, 1):
            summary_parts.append(f"{i}. Q: {entry['question']}")
            summary_parts.append(f"   A: {entry['answer']}")
            summary_parts.append("")

        summary = "\n".join(summary_parts)
        
        # Calculate token usage for summary
        summary_tokens = count_tokens(summary)
        
        # Log summary generation metrics
        logger.info("Generated conversation summary", extra={
            "component": "memory",
            "operation": "get_conversation_summary",
            "session_id": session_id,
            "summary_length": len(summary),
            "summary_tokens": summary_tokens,
            "interactions_in_summary": len(recent_context),
            "processing_time_ms": (time.time() - start_time) * 1000,
            "optimization": "context_excluded_from_summary",
            "note": "full_answers_included"
        })
        
        return summary

    async def get_conversation_summary_async(self, session_id: str) -> str:
        """
        Get a summary of the conversation history asynchronously.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Summary of the conversation
        """
        logger.info("Generating conversation summary (async)", extra={
            "component": "memory",
            "operation": "get_conversation_summary_async",
            "session_id": session_id
        })
        return await asyncio.to_thread(self.get_conversation_summary, session_id)

    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a specific session.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self.conversations:
            interactions_cleared = len(self.conversations[session_id])
            del self.conversations[session_id]
            
            logger.info("Cleared conversation memory for session", extra={
                "component": "memory",
                "operation": "clear_session",
                "session_id": session_id,
                "interactions_cleared": interactions_cleared,
                "remaining_sessions": len(self.conversations)
            })
        else:
            logger.info("No memory found for session to clear", extra={
                "component": "memory",
                "operation": "clear_session",
                "session_id": session_id,
                "status": "not_found"
            })

    async def clear_session_async(self, session_id: str) -> None:
        """
        Clear conversation history for a specific session asynchronously.
        
        Args:
            session_id: Unique session identifier
        """
        logger.info("Clearing conversation memory for session (async)", extra={
            "component": "memory",
            "operation": "clear_session_async",
            "session_id": session_id
        })
        return await asyncio.to_thread(self.clear_session, session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        total_sessions = len(self.conversations)
        total_interactions = sum(len(conv) for conv in self.conversations.values())
        
        # Calculate memory usage
        total_memory_bytes = 0
        total_tokens_saved = 0
        
        for session_id, interactions in self.conversations.items():
            session_data = json.dumps(interactions)
            total_memory_bytes += len(session_data.encode('utf-8'))
            
            # Estimate tokens saved by not storing context
            for interaction in interactions:
                # Estimate what context would have been (rough estimate)
                estimated_context_length = len(interaction.get('question', '')) * 10  # Rough estimate
                total_tokens_saved += count_tokens("x" * estimated_context_length)
        
        stats = {
            "enabled": Config.MEMORY_ENABLED,
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "max_entries": self.max_entries,
            "max_age_hours": self.max_age_seconds / 3600,
            "memory_type": "in_memory",
            "total_memory_bytes": total_memory_bytes,
            "total_tokens_saved": total_tokens_saved,
            "optimization": "context_removed"
        }
        
        logger.info("Retrieved memory statistics", extra={
            "component": "memory",
            "operation": "get_memory_stats",
            **stats
        })
        
        return stats

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """
        Get memory usage statistics asynchronously.
        
        Returns:
            Dictionary with memory statistics
        """
        logger.info("Retrieving memory statistics (async)", extra={
            "component": "memory",
            "operation": "get_memory_stats_async"
        })
        return await asyncio.to_thread(self.get_memory_stats)

    def _cleanup_old_entries(self, session_id: str) -> None:
        """
        Remove old entries from memory.
        
        Args:
            session_id: Unique session identifier
        """
        if session_id not in self.conversations:
            return

        current_time = time.time()
        original_count = len(self.conversations[session_id])
        
        valid_entries = [
            entry
            for entry in self.conversations[session_id]
            if current_time - entry["timestamp"] < self.max_age_seconds
        ]

        # Keep only the most recent entries up to max_entries
        if len(valid_entries) > self.max_entries:
            valid_entries = valid_entries[-self.max_entries :]

        self.conversations[session_id] = valid_entries
        
        cleaned_count = original_count - len(valid_entries)
        
        if cleaned_count > 0:
            logger.info("Cleaned up old memory entries", extra={
                "component": "memory",
                "operation": "cleanup_old_entries",
                "session_id": session_id,
                "original_count": original_count,
                "final_count": len(valid_entries),
                "entries_removed": cleaned_count,
                "max_entries": self.max_entries,
                "max_age_seconds": self.max_age_seconds
            }) 