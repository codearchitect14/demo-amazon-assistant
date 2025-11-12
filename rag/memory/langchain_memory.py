"""
LangChain memory implementation for conversation management.
"""

import logging
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from app.config import Config
from rag.memory.base import MemoryStrategy

logger = logging.getLogger(__name__)


class LangChainConversationMemory(MemoryStrategy):
    """
    LangChain-based conversation memory implementation.
    
    This implementation uses LangChain's memory components for
    more advanced conversation management features.
    """

    def __init__(self, max_entries: int = Config.MEMORY_MAX_ENTRIES, max_age_hours: int = Config.MEMORY_MAX_AGE_HOURS):
        """Initialize LangChain conversation memory."""
        self.max_entries = max_entries
        self.max_age_hours = max_age_hours
        self.sessions = {}
        
        # Structured logging for initialization
        logger.info("LangChainConversationMemory initialized", extra={
            "component": "memory",
            "memory_type": "langchain",
            "max_entries": max_entries,
            "max_age_hours": max_age_hours,
            "optimization": "context_removed"
        })

    def add_interaction(
        self, 
        session_id: str, 
        question: str, 
        answer: str, 
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an interaction to memory."""
        start_time = time.time()
        
        logger.info("Adding interaction to LangChain memory", extra={
            "component": "memory",
            "operation": "add_interaction",
            "memory_type": "langchain",
            "session_id": session_id,
            "question_length": len(question),
            "answer_length": len(answer),
            "context_length": len(context),
            "has_metadata": metadata is not None,
            "optimization": "context_not_stored"
        })
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            logger.info("Creating new LangChain conversation list for session", extra={
                "component": "memory",
                "operation": "create_session",
                "memory_type": "langchain",
                "session_id": session_id,
                "total_sessions": len(self.sessions)
            })
        
        # Only store essential conversation data - not the context
        interaction = {
            "question": question,
            "answer": answer,
            "metadata": metadata or {},
            "timestamp": asyncio.get_event_loop().time()
            # Note: context is not stored to save memory and reduce token usage
        }
        
        self.sessions[session_id].append(interaction)
        
        # Maintain max entries limit
        if len(self.sessions[session_id]) > self.max_entries:
            removed_count = len(self.sessions[session_id]) - self.max_entries
            self.sessions[session_id] = self.sessions[session_id][-self.max_entries:]
            logger.info("Trimmed LangChain memory to max entries", extra={
                "component": "memory",
                "operation": "trim_memory",
                "memory_type": "langchain",
                "session_id": session_id,
                "entries_removed": removed_count,
                "max_entries": self.max_entries
            })
        
        # Calculate memory usage metrics
        interaction_size = len(json.dumps(interaction))
        session_size = len(json.dumps(self.sessions[session_id]))
        total_interactions = len(self.sessions[session_id])
        
        logger.info("Successfully added interaction to LangChain memory", extra={
            "component": "memory",
            "operation": "add_interaction",
            "memory_type": "langchain",
            "session_id": session_id,
            "interaction_size_bytes": interaction_size,
            "session_size_bytes": session_size,
            "total_interactions": total_interactions,
            "context_optimization": "enabled",
            "context_saved_bytes": len(context),
            "processing_time_ms": (time.time() - start_time) * 1000
        })

    async def add_interaction_async(
        self, 
        session_id: str, 
        question: str, 
        answer: str, 
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an interaction to memory asynchronously."""
        logger.info("Adding interaction to LangChain memory (async)", extra={
            "component": "memory",
            "operation": "add_interaction_async",
            "memory_type": "langchain",
            "session_id": session_id,
            "question_length": len(question),
            "answer_length": len(answer),
            "context_length": len(context)
        })
        self.add_interaction(session_id, question, answer, context, metadata)

    def get_recent_context(self, session_id: str, max_entries: int = None) -> List[Dict[str, Any]]:
        """Get recent conversation context."""
        start_time = time.time()
        
        logger.info("Getting recent LangChain conversation context", extra={
            "component": "memory",
            "operation": "get_recent_context",
            "memory_type": "langchain",
            "session_id": session_id,
            "max_entries": max_entries
        })
        
        if session_id not in self.sessions:
            logger.info("No LangChain conversation history found for session", extra={
                "component": "memory",
                "operation": "get_recent_context",
                "memory_type": "langchain",
                "session_id": session_id,
                "result": "empty_list"
            })
            return []
        
        entries = self.sessions[session_id]
        
        # Filter expired entries
        current_time = asyncio.get_event_loop().time()
        valid_entries = [
            entry for entry in entries
            if current_time - entry["timestamp"] < (self.max_age_hours * 3600)
        ]
        
        if max_entries:
            valid_entries = valid_entries[-max_entries:]
        
        # Calculate metrics
        total_entries = len(entries)
        expired_entries = len(entries) - len(valid_entries)
        context_size = len(json.dumps(valid_entries))
        
        logger.info("Retrieved recent LangChain conversation context", extra={
            "component": "memory",
            "operation": "get_recent_context",
            "memory_type": "langchain",
            "session_id": session_id,
            "total_entries_in_session": total_entries,
            "requested_entries": max_entries,
            "valid_entries_returned": len(valid_entries),
            "expired_entries_filtered": expired_entries,
            "context_size_bytes": context_size,
            "processing_time_ms": (time.time() - start_time) * 1000
        })
        
        return valid_entries

    async def get_recent_context_async(self, session_id: str, max_entries: int = None) -> List[Dict[str, Any]]:
        """Get recent conversation context asynchronously."""
        logger.info("Getting recent LangChain conversation context (async)", extra={
            "component": "memory",
            "operation": "get_recent_context_async",
            "memory_type": "langchain",
            "session_id": session_id,
            "max_entries": max_entries
        })
        return self.get_recent_context(session_id, max_entries)

    def clear_session(self, session_id: str) -> None:
        """Clear memory for a specific session."""
        if session_id in self.sessions:
            interactions_cleared = len(self.sessions[session_id])
            del self.sessions[session_id]
            
            logger.info("Cleared LangChain memory for session", extra={
                "component": "memory",
                "operation": "clear_session",
                "memory_type": "langchain",
                "session_id": session_id,
                "interactions_cleared": interactions_cleared,
                "remaining_sessions": len(self.sessions)
            })
        else:
            logger.info("No LangChain memory found for session to clear", extra={
                "component": "memory",
                "operation": "clear_session",
                "memory_type": "langchain",
                "session_id": session_id,
                "status": "not_found"
            })

    async def clear_session_async(self, session_id: str) -> None:
        """Clear memory for a specific session asynchronously."""
        logger.info("Clearing LangChain memory for session (async)", extra={
            "component": "memory",
            "operation": "clear_session_async",
            "memory_type": "langchain",
            "session_id": session_id
        })
        self.clear_session(session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_sessions = len(self.sessions)
        total_interactions = sum(len(interactions) for interactions in self.sessions.values())
        
        # Calculate memory usage
        total_memory_bytes = 0
        for session_id, interactions in self.sessions.items():
            session_data = json.dumps(interactions)
            total_memory_bytes += len(session_data.encode('utf-8'))
        
        stats = {
            "memory_type": "langchain",
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "max_entries": self.max_entries,
            "max_age_hours": self.max_age_hours,
            "total_memory_bytes": total_memory_bytes,
            "session_ids": list(self.sessions.keys()),
            "optimization": "context_removed"
        }
        
        logger.info("Retrieved LangChain memory statistics", extra={
            "component": "memory",
            "operation": "get_memory_stats",
            "memory_type": "langchain",
            **stats
        })
        
        return stats

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory statistics asynchronously."""
        logger.info("Retrieving LangChain memory statistics (async)", extra={
            "component": "memory",
            "operation": "get_memory_stats_async",
            "memory_type": "langchain"
        })
        return self.get_memory_stats()

    def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation for a session."""
        start_time = time.time()
        
        logger.info("Generating LangChain conversation summary", extra={
            "component": "memory",
            "operation": "get_conversation_summary",
            "memory_type": "langchain",
            "session_id": session_id
        })
        
        if session_id not in self.sessions:
            logger.info("No LangChain memory found for session summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "memory_type": "langchain",
                "session_id": session_id,
                "result": "empty_summary"
            })
            return ""
        
        interactions = self.sessions[session_id]
        if not interactions:
            logger.info("No interactions found for LangChain summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "memory_type": "langchain",
                "session_id": session_id,
                "result": "empty_summary"
            })
            return ""
        
        summary_parts = []
        for interaction in interactions[-5:]:  # Last 5 interactions
            summary_parts.append(f"Q: {interaction['question']}")
            summary_parts.append(f"A: {interaction['answer']}")
        
        summary = "\n".join(summary_parts)
        
        # Log summary generation metrics
        logger.info("Generated LangChain conversation summary", extra={
            "component": "memory",
            "operation": "get_conversation_summary",
            "memory_type": "langchain",
            "session_id": session_id,
            "summary_length": len(summary),
            "interactions_in_summary": len(interactions[-5:]),
            "processing_time_ms": (time.time() - start_time) * 1000,
            "optimization": "context_excluded_from_summary"
        })
        
        return summary

    async def get_conversation_summary_async(self, session_id: str) -> str:
        """Get a summary of the conversation for a session asynchronously."""
        logger.info("Generating LangChain conversation summary (async)", extra={
            "component": "memory",
            "operation": "get_conversation_summary_async",
            "memory_type": "langchain",
            "session_id": session_id
        })
        return self.get_conversation_summary(session_id) 