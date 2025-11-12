import os
import logging
import json
import time
import random
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from groq import Groq
from groq import AsyncGroq
from app.config import Config
from prompts import get_rag_system_prompt, build_rag_user_prompt
from rich_logging import (
    log_pipeline_step, log_token_breakdown, log_prompt_analysis,
    log_memory_operation, log_agent_decision, log_final_summary,
    log_what_sent_to_llm, log_comprehensive_token_breakdown, count_tokens
)

# LangChain imports for conversation memory
try:
    from langchain.memory import ConversationBufferMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    from langchain_core.messages import BaseMessage as CoreBaseMessage

    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain imports failed: {e}")

    # Create fallback classes
    class ConversationBufferMemory:
        def __init__(self, **kwargs):
            self.chat_memory = type(
                "ChatMemory",
                (),
                {
                    "messages": [],
                    "add_user_message": lambda self, msg: self.messages.append(
                        type("Message", (), {"content": msg, "type": "human"})()
                    ),
                    "add_ai_message": lambda self, msg: self.messages.append(
                        type("Message", (), {"content": msg, "type": "ai"})()
                    ),
                },
            )()

    class BaseMessage:
        def __init__(self, content=""):
            self.content = content

    class HumanMessage(BaseMessage):
        pass

    class AIMessage(BaseMessage):
        pass

    class CoreBaseMessage(BaseMessage):
        pass

    LANGCHAIN_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Validate environment variables
Config.validate_required_configs()


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling failures gracefully
    """

    def __init__(
        self,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = (
            failure_threshold or Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        )
        self.recovery_timeout = (
            recovery_timeout or Config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise e

    async def call_async(self, func, *args, **kwargs):
        """Execute async function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise e

    def on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker transitioning to CLOSED state")

    def on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.
    Supports both sync and async operations.
    """

    def __init__(
        self, max_retries: int = None, base_delay: float = None, max_delay: float = None
    ):
        self.max_retries = max_retries or 3
        self.base_delay = base_delay or 1.0
        self.max_delay = max_delay or 60.0

    def call_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic - SYNC VERSION"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    logger.error(
                        f"All {self.max_retries} retry attempts failed. Last error: {e}"
                    )
                    raise e

                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2**attempt), self.max_delay)
                jitter = random.uniform(0, 0.1 * delay)
                total_delay = delay + jitter

                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.2f}s"
                )
                # Use time.sleep for sync context
                time.sleep(total_delay)

        raise last_exception

    async def call_with_retry_async(self, func, *args, **kwargs):
        """Execute async function with retry logic"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    logger.error(
                        f"All {self.max_retries} retry attempts failed. Last error: {e}"
                    )
                    raise e

                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2**attempt), self.max_delay)
                jitter = random.uniform(0, 0.1 * delay)
                total_delay = delay + jitter

                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.2f}s"
                )
                await asyncio.sleep(total_delay)

        raise last_exception


class LLMClient:
    """
    Robust LLM client with circuit breaker, retry logic, and graceful degradation
    """

    def __init__(
        self,
        primary_api_key: str,
        primary_model: str = "llama-3.3-70b-versatile",
        fallback_api_key: str = None,
        fallback_model: str = "llama-3.1-8b-instant",
        enable_circuit_breaker: bool = True,
        enable_retry: bool = True,
    ):

        self.primary_api_key = primary_api_key
        self.primary_model = primary_model
        self.fallback_api_key = fallback_api_key
        self.fallback_model = fallback_model

        # Initialize circuit breaker and retry handler
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        self.retry_handler = RetryHandler() if enable_retry else None

        # Health tracking
        self.primary_failures = 0
        self.fallback_failures = 0
        self.last_primary_failure = None
        self.last_fallback_failure = None

        # Initialize both sync and async clients
        self.primary_client = (
            Groq(api_key=primary_api_key) if primary_api_key and primary_api_key != "None" else None
        )
        self.fallback_client = (
            Groq(api_key=fallback_api_key) if fallback_api_key and fallback_api_key != "None" else None
        )
        self.primary_client_async = (
            AsyncGroq(api_key=primary_api_key) if primary_api_key and primary_api_key != "None" else None
        )
        self.fallback_client_async = (
            AsyncGroq(api_key=fallback_api_key) if fallback_api_key and fallback_api_key != "None" else None
        )

        logger.info(
            f"LLM Client initialized with primary model: {primary_model}"
        )
        if fallback_api_key:
            logger.info(f"Fallback model configured: {fallback_model}")
        else:
            logger.info("No fallback model configured")

    async def _make_request_async(
        self, client: AsyncGroq, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """Make async request to Groq API"""
        try:
            response = await client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in async request to {model}: {e}")
            raise e

    async def generate_response_async(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """Generate response using async Groq API with fallback support"""
        # Try primary model first
        if self.primary_client_async and self.primary_model:
            try:
                if self.circuit_breaker:
                    response = await self.circuit_breaker.call_async(
                        self._make_request_async,
                        self.primary_client_async,
                        self.primary_model,
                        messages,
                        **kwargs,
                    )
                elif self.retry_handler:
                    response = await self.retry_handler.call_with_retry_async(
                        self._make_request_async,
                        self.primary_client_async,
                        self.primary_model,
                        messages,
                        **kwargs,
                    )
                else:
                    response = await self._make_request_async(
                        self.primary_client_async,
                        self.primary_model,
                        messages,
                        **kwargs,
                    )

                self.primary_failures = 0
                return response

            except Exception as e:
                self.primary_failures += 1
                self.last_primary_failure = time.time()
                logger.warning(
                    f"Primary model failed ({self.primary_failures} failures): {e}"
                )

        # Try fallback model
        if self.fallback_client_async and self.fallback_model and self.fallback_api_key:
            logger.info(f"Attempting fallback to model: {self.fallback_model}")
            try:
                if self.circuit_breaker:
                    response = await self.circuit_breaker.call_async(
                        self._make_request_async,
                        self.fallback_client_async,
                        self.fallback_model,
                        messages,
                        **kwargs,
                    )
                elif self.retry_handler:
                    response = await self.retry_handler.call_with_retry_async(
                        self._make_request_async,
                        self.fallback_client_async,
                        self.fallback_model,
                        messages,
                        **kwargs,
                    )
                else:
                    response = await self._make_request_async(
                        self.fallback_client_async,
                        self.fallback_model,
                        messages,
                        **kwargs,
                    )

                self.fallback_failures = 0
                logger.info("Successfully used fallback model")
                return response

            except Exception as e:
                self.fallback_failures += 1
                self.last_fallback_failure = time.time()
                logger.error(
                    f"Fallback model also failed ({self.fallback_failures} failures): {e}"
                )
        else:
            logger.warning("No fallback model available - skipping fallback attempt")

        # If both models fail
        raise Exception("Both primary and fallback models failed")

    async def generate_response_stream_async(
        self, messages: List[Dict[str, str]], **kwargs
    ):
        """Generate streaming response using async Groq API with fallback support"""
        # Try primary model first
        if self.primary_client_async and self.primary_model:
            try:
                async for chunk in self._make_streaming_request_async(
                    self.primary_client_async, self.primary_model, messages, **kwargs
                ):
                    yield chunk

                self.primary_failures = 0
                return

            except Exception as e:
                self.primary_failures += 1
                self.last_primary_failure = time.time()
                logger.warning(
                    f"Primary model failed ({self.primary_failures} failures): {e}"
                )

        # Try fallback model
        if self.fallback_client_async and self.fallback_model and self.fallback_api_key:
            logger.info(f"Attempting fallback to model: {self.fallback_model}")
            try:
                async for chunk in self._make_streaming_request_async(
                    self.fallback_client_async, self.fallback_model, messages, **kwargs
                ):
                    yield chunk

                self.fallback_failures = 0
                logger.info("Successfully used fallback model")
                return

            except Exception as e:
                self.fallback_failures += 1
                self.last_fallback_failure = time.time()
                logger.error(
                    f"Fallback model also failed ({self.fallback_failures} failures): {e}"
                )
        else:
            logger.warning("No fallback model available - skipping fallback attempt")

        # If both models fail
        raise Exception("Both primary and fallback models failed")

    async def _make_streaming_request_async(
        self, client: AsyncGroq, model: str, messages: List[Dict[str, str]], **kwargs
    ):
        """Make async streaming request to Groq API"""
        try:
            response = await client.chat.completions.create(
                model=model, messages=messages, stream=True, **kwargs
            )

            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error in async streaming request to {model}: {e}")
            raise e

    def _make_request(
        self, client: Groq, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """Make synchronous request to Groq API (for backward compatibility)"""
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in request to {model}: {e}")
            raise e

    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using synchronous Groq API with fallback support (for backward compatibility)"""
        # Try primary model first
        if self.primary_client and self.primary_model:
            try:
                if self.circuit_breaker:
                    response = self.circuit_breaker.call(
                        self._make_request,
                        self.primary_client,
                        self.primary_model,
                        messages,
                        **kwargs,
                    )
                elif self.retry_handler:
                    response = self.retry_handler.call_with_retry(
                        self._make_request,
                        self.primary_client,
                        self.primary_model,
                        messages,
                        **kwargs,
                    )
                else:
                    response = self._make_request(
                        self.primary_client, self.primary_model, messages, **kwargs
                    )

                self.primary_failures = 0
                return response

            except Exception as e:
                self.primary_failures += 1
                self.last_primary_failure = time.time()
                logger.warning(
                    f"Primary model failed ({self.primary_failures} failures): {e}"
                )

        # Try fallback model
        if self.fallback_client and self.fallback_model and self.fallback_api_key:
            logger.info(f"Attempting fallback to model: {self.fallback_model}")
            try:
                if self.circuit_breaker:
                    response = self.circuit_breaker.call(
                        self._make_request,
                        self.fallback_client,
                        self.fallback_model,
                        messages,
                        **kwargs,
                    )
                elif self.retry_handler:
                    response = self.retry_handler.call_with_retry(
                        self._make_request,
                        self.fallback_client,
                        self.fallback_model,
                        messages,
                        **kwargs,
                    )
                else:
                    response = self._make_request(
                        self.fallback_client, self.fallback_model, messages, **kwargs
                    )

                self.fallback_failures = 0
                logger.info("Successfully used fallback model")
                return response

            except Exception as e:
                self.fallback_failures += 1
                self.last_fallback_failure = time.time()
                logger.error(
                    f"Fallback model also failed ({self.fallback_failures} failures): {e}"
                )
        else:
            logger.warning("No fallback model available - skipping fallback attempt")

        # If both models fail
        raise Exception("Both primary and fallback models failed")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of LLM client"""
        return {
            "primary_failures": self.primary_failures,
            "fallback_failures": self.fallback_failures,
            "last_primary_failure": self.last_primary_failure,
            "last_fallback_failure": self.last_fallback_failure,
            "circuit_breaker_state": (
                self.circuit_breaker.get_state() if self.circuit_breaker else None
            ),
            "primary_available": self.primary_client is not None,
            "fallback_available": self.fallback_client is not None,
            "primary_async_available": self.primary_client_async is not None,
            "fallback_async_available": self.fallback_client_async is not None,
        }

    async def get_health_status_async(self) -> Dict[str, Any]:
        """Get health status of LLM client (async version)"""
        return self.get_health_status()

    def reset_health(self):
        """Reset health status"""
        self.primary_failures = 0
        self.fallback_failures = 0
        self.last_primary_failure = None
        self.last_fallback_failure = None
        if self.circuit_breaker:
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.state = "CLOSED"
        logger.info("LLM client health status reset")


# Initialize robust LLM client
try:
    # Only use fallback if API key is provided and not empty
    fallback_api_key = Config.GROQ_FALLBACK_API_KEY if Config.GROQ_FALLBACK_API_KEY and Config.GROQ_FALLBACK_API_KEY.strip() else None
    
    llm_client = LLMClient(
        primary_api_key=Config.GROQ_API_KEY,
        primary_model=Config.GROQ_PRIMARY_MODEL,
        fallback_api_key=fallback_api_key,
        fallback_model=Config.GROQ_FALLBACK_MODEL,
        enable_circuit_breaker=Config.ENABLE_CIRCUIT_BREAKER,
        enable_retry=Config.ENABLE_RETRY_LOGIC,
    )
    logger.info(f"Robust LLM client initialized successfully with primary model: {Config.GROQ_PRIMARY_MODEL}")
    if fallback_api_key:
        logger.info(f"Fallback model configured: {Config.GROQ_FALLBACK_MODEL}")
    else:
        logger.info("No fallback model configured")
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {e}")
    raise


class ConversationMemory:
    """
    Simple in-memory conversation history manager
    """

    def __init__(
        self,
        max_entries: int = Config.MEMORY_MAX_ENTRIES,
        max_age_hours: int = Config.MEMORY_MAX_AGE_HOURS,
    ):
        self.max_entries = max_entries
        self.max_age_seconds = max_age_hours * 3600
        self.conversations = {}  # session_id -> conversation_history

    def add_interaction(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Dict[str, Any] = None,
    ):
        """Add a new interaction to the conversation memory"""
        logger.info(
            f"ConversationMemory.add_interaction called for session: {session_id}"
        )
        if not Config.MEMORY_ENABLED:
            logger.warning("Memory not enabled in config")
            return

        if session_id not in self.conversations:
            logger.info(f"Creating new conversation list for session: {session_id}")
            self.conversations[session_id] = []

        # Only store essential conversation data - not the context
        interaction = {
            "timestamp": time.time(),
            "question": question,
            "answer": answer,
            "metadata": metadata or {},
            # Note: context is not stored to save memory and reduce token usage
        }

        self.conversations[session_id].append(interaction)
        logger.info(
            f"Added interaction to memory. Session {session_id} now has {len(self.conversations[session_id])} interactions"
        )

        # Clean up old entries
        self._cleanup_old_entries(session_id)

        logger.info(f"Added interaction to memory for session {session_id}")

    async def add_interaction_async(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",
        metadata: Dict[str, Any] = None,
    ):
        """Add a new interaction to the conversation memory (async)"""
        logger.info(
            f"ConversationMemory.add_interaction_async called for session: {session_id}"
        )
        return await asyncio.to_thread(
            self.add_interaction, session_id, question, answer, context, metadata
        )

    def get_recent_context(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context for a session"""
        logger.info(
            f"ConversationMemory.get_recent_context called for session: {session_id}, max_entries: {max_entries}"
        )
        if not Config.MEMORY_ENABLED or session_id not in self.conversations:
            logger.info(
                f"Memory not enabled or session not found. enabled={Config.MEMORY_ENABLED}, session_exists={session_id in self.conversations}"
            )
            return []

        # Get recent entries, excluding the current interaction
        recent = self.conversations[session_id][-max_entries:]
        logger.info(
            f"Found {len(recent)} recent interactions for session: {session_id}"
        )

        # Filter out expired entries
        current_time = time.time()
        valid_entries = [
            entry
            for entry in recent
            if current_time - entry["timestamp"] < self.max_age_seconds
        ]

        logger.info(
            f"After filtering expired entries: {len(valid_entries)} valid interactions"
        )
        return valid_entries

    async def get_recent_context_async(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context for a session (async)"""
        logger.info(
            f"ConversationMemory.get_recent_context_async called for session: {session_id}"
        )
        return await asyncio.to_thread(self.get_recent_context, session_id, max_entries)

    def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation history"""
        logger.info(
            f"ConversationMemory.get_conversation_summary called for session: {session_id}"
        )
        if not Config.MEMORY_ENABLED or session_id not in self.conversations:
            logger.info(
                f"Memory not enabled or session not found. enabled={Config.MEMORY_ENABLED}, session_exists={session_id in self.conversations}"
            )
            return ""

        recent_context = self.get_recent_context(session_id, max_entries=5)
        logger.info(f"Retrieved {len(recent_context)} recent interactions for summary")

        if not recent_context:
            logger.info("No recent context found for summary")
            return ""

        summary_parts = ["Previous conversation context:"]

        for i, entry in enumerate(recent_context, 1):
            summary_parts.append(f"{i}. Q: {entry['question']}")
            summary_parts.append(f"   A: {entry['answer']}")
            summary_parts.append("")

        summary = "\n".join(summary_parts)
        logger.info(f"Generated conversation summary with {len(summary)} characters")
        return summary

    async def get_conversation_summary_async(self, session_id: str) -> str:
        """Get a summary of the conversation history (async)"""
        logger.info(
            f"ConversationMemory.get_conversation_summary_async called for session: {session_id}"
        )
        return await asyncio.to_thread(self.get_conversation_summary, session_id)

    def _cleanup_old_entries(self, session_id: str):
        """Remove old entries from memory"""
        if session_id not in self.conversations:
            return

        current_time = time.time()
        valid_entries = [
            entry
            for entry in self.conversations[session_id]
            if current_time - entry["timestamp"] < self.max_age_seconds
        ]

        # Keep only the most recent entries up to max_entries
        if len(valid_entries) > self.max_entries:
            valid_entries = valid_entries[-self.max_entries :]

        self.conversations[session_id] = valid_entries

    def clear_session(self, session_id: str):
        """Clear conversation history for a specific session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared memory for session {session_id}")

    async def clear_session_async(self, session_id: str):
        """Clear conversation history for a specific session (async)"""
        return await asyncio.to_thread(self.clear_session, session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        total_sessions = len(self.conversations)
        total_interactions = sum(len(conv) for conv in self.conversations.values())

        return {
            "enabled": Config.MEMORY_ENABLED,
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "max_entries": self.max_entries,
            "max_age_hours": self.max_age_seconds / 3600,
        }

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory usage statistics (async)"""
        return await asyncio.to_thread(self.get_memory_stats)


class RedisConversationMemory:
    """
    Redis-based conversation history manager with TTL and proper cleanup
    """

    def __init__(
        self,
        redis_url: str = Config.REDIS_URL,
        ttl_hours: int = Config.REDIS_TTL_HOURS,
        max_entries: int = Config.REDIS_MAX_ENTRIES,
    ):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_hours * 3600
        self.max_entries = max_entries
        self.redis = None
        self.redis_available = False

        try:
            import redis

            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            self.redis_available = True
            logger.info(f"Redis connection established: {redis_url}")
        except ImportError:
            logger.warning(
                "Redis package not installed. Install with: pip install redis"
            )
            self.redis_available = False
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Falling back to in-memory storage."
            )
            self.redis_available = False

    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"conversation:{session_id}"

    def _get_interaction_key(self, session_id: str, interaction_id: str) -> str:
        """Generate Redis key for specific interaction"""
        return f"interaction:{session_id}:{interaction_id}"

    def add_interaction(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Dict[str, Any] = None,
    ):
        """Add a new interaction to the conversation memory"""
        start_time = time.time()
        
        logger.info("Adding interaction to Redis memory", extra={
            "component": "memory",
            "operation": "add_interaction",
            "memory_type": "redis",
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
                "memory_type": "redis",
                "session_id": session_id,
                "status": "skipped"
            })
            return

        if not self.redis_available:
            logger.warning("Redis not available, skipping interaction storage", extra={
                "component": "memory",
                "operation": "add_interaction",
                "memory_type": "redis",
                "session_id": session_id,
                "status": "redis_unavailable"
            })
            return

        try:
            import uuid
            import json

            interaction_id = str(uuid.uuid4())
            # Only store essential conversation data - not the context
            interaction = {
                "id": interaction_id,
                "timestamp": time.time(),
                "question": question,
                "answer": answer,
                "metadata": metadata or {},
                # Note: context is not stored to save memory and reduce token usage
            }

            # Store interaction
            interaction_key = self._get_interaction_key(session_id, interaction_id)
            self.redis.setex(interaction_key, self.ttl_seconds, json.dumps(interaction))

            # Update session list
            session_key = self._get_session_key(session_id)
            self.redis.lpush(session_key, interaction_id)
            self.redis.expire(session_key, self.ttl_seconds)

            # Trim to max entries
            self.redis.ltrim(session_key, 0, self.max_entries - 1)

            # Calculate memory usage metrics
            interaction_size = len(json.dumps(interaction))
            context_saved = len(context)
            
            logger.info("Successfully added interaction to Redis memory", extra={
                "component": "memory",
                "operation": "add_interaction",
                "memory_type": "redis",
                "session_id": session_id,
                "interaction_id": interaction_id,
                "interaction_size_bytes": interaction_size,
                "context_optimization": "enabled",
                "context_saved_bytes": context_saved,
                "ttl_seconds": self.ttl_seconds,
                "max_entries": self.max_entries,
                "processing_time_ms": (time.time() - start_time) * 1000
            })

        except Exception as e:
            logger.error("Error adding interaction to Redis", extra={
                "component": "memory",
                "operation": "add_interaction",
                "memory_type": "redis",
                "session_id": session_id,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            })

    async def add_interaction_async(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",
        metadata: Dict[str, Any] = None,
    ):
        """Add an interaction to the conversation memory (async)"""
        return await asyncio.to_thread(
            self.add_interaction, session_id, question, answer, context, metadata
        )

    def get_recent_context(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context for a session"""
        start_time = time.time()
        
        logger.info("Getting recent Redis conversation context", extra={
            "component": "memory",
            "operation": "get_recent_context",
            "memory_type": "redis",
            "session_id": session_id,
            "max_entries": max_entries
        })
        
        if not Config.MEMORY_ENABLED or not self.redis_available:
            logger.info("Memory not enabled or Redis not available", extra={
                "component": "memory",
                "operation": "get_recent_context",
                "memory_type": "redis",
                "session_id": session_id,
                "memory_enabled": Config.MEMORY_ENABLED,
                "redis_available": self.redis_available,
                "result": "empty_list"
            })
            return []

        try:
            import json

            session_key = self._get_session_key(session_id)
            interaction_ids = self.redis.lrange(session_key, 0, max_entries - 1)

            interactions = []
            current_time = time.time()

            for interaction_id in interaction_ids:
                interaction_key = self._get_interaction_key(session_id, interaction_id)
                interaction_data = self.redis.get(interaction_key)

                if interaction_data:
                    interaction = json.loads(interaction_data)
                    # Check if interaction is still valid (within TTL)
                    if current_time - interaction["timestamp"] < self.ttl_seconds:
                        interactions.append(interaction)

            # Sort by timestamp (most recent first)
            interactions.sort(key=lambda x: x["timestamp"], reverse=True)
            result = interactions[:max_entries]
            
            # Calculate metrics
            total_interactions = len(interaction_ids)
            valid_interactions = len(interactions)
            expired_interactions = total_interactions - valid_interactions
            context_size = len(json.dumps(result))
            
            logger.info("Retrieved recent Redis conversation context", extra={
                "component": "memory",
                "operation": "get_recent_context",
                "memory_type": "redis",
                "session_id": session_id,
                "total_interactions_found": total_interactions,
                "valid_interactions_returned": len(result),
                "expired_interactions_filtered": expired_interactions,
                "context_size_bytes": context_size,
                "processing_time_ms": (time.time() - start_time) * 1000
            })

            return result

        except Exception as e:
            logger.error("Error getting recent context from Redis", extra={
                "component": "memory",
                "operation": "get_recent_context",
                "memory_type": "redis",
                "session_id": session_id,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            })
            return []

    async def get_recent_context_async(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context for a session (async)"""
        return await asyncio.to_thread(self.get_recent_context, session_id, max_entries)

    def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation history"""
        start_time = time.time()
        
        logger.info("Generating Redis conversation summary", extra={
            "component": "memory",
            "operation": "get_conversation_summary",
            "memory_type": "redis",
            "session_id": session_id
        })
        
        if not Config.MEMORY_ENABLED or not self.redis_available:
            logger.info("Memory not enabled or Redis not available for summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "memory_type": "redis",
                "session_id": session_id,
                "memory_enabled": Config.MEMORY_ENABLED,
                "redis_available": self.redis_available,
                "result": "empty_summary"
            })
            return ""

        try:
            import json

            session_key = self._get_session_key(session_id)
            interaction_ids = self.redis.lrange(session_key, 0, 9)  # Get last 10 interactions

            if not interaction_ids:
                logger.info("No interactions found for Redis summary", extra={
                    "component": "memory",
                    "operation": "get_conversation_summary",
                    "memory_type": "redis",
                    "session_id": session_id,
                    "result": "empty_summary"
                })
                return ""

            interactions = []
            current_time = time.time()

            for interaction_id in interaction_ids:
                interaction_key = self._get_interaction_key(session_id, interaction_id)
                interaction_data = self.redis.get(interaction_key)

                if interaction_data:
                    interaction = json.loads(interaction_data)
                    if current_time - interaction["timestamp"] < self.ttl_seconds:
                        interactions.append(interaction)

            if not interactions:
                logger.info("No valid interactions found for Redis summary", extra={
                    "component": "memory",
                    "operation": "get_conversation_summary",
                    "memory_type": "redis",
                    "session_id": session_id,
                    "result": "empty_summary"
                })
                return ""

            # Create summary
            summary_parts = ["Previous conversation context:"]
            for i, interaction in enumerate(interactions[-5:], 1):  # Last 5 interactions
                summary_parts.append(f"{i}. Q: {interaction['question']}")
                summary_parts.append(f"   A: {interaction['answer']}")
                summary_parts.append("")

            summary = "\n".join(summary_parts)
            
            # Log summary generation metrics
            logger.info("Generated Redis conversation summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "memory_type": "redis",
                "session_id": session_id,
                "summary_length": len(summary),
                "interactions_in_summary": len(interactions[-5:]),
                "total_interactions_found": len(interaction_ids),
                "valid_interactions": len(interactions),
                "processing_time_ms": (time.time() - start_time) * 1000,
                "optimization": "context_excluded_from_summary",
                "note": "full_answers_included"
            })

            return summary

        except Exception as e:
            logger.error("Error generating Redis conversation summary", extra={
                "component": "memory",
                "operation": "get_conversation_summary",
                "memory_type": "redis",
                "session_id": session_id,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            })
            return ""

    async def get_conversation_summary_async(self, session_id: str) -> str:
        """Get a summary of the conversation history (async)"""
        return await asyncio.to_thread(self.get_conversation_summary, session_id)

    def clear_session(self, session_id: str):
        """Clear conversation history for a specific session"""
        if not self.redis_available:
            return

        try:
            session_key = self._get_session_key(session_id)
            interaction_ids = self.redis.lrange(session_key, 0, -1)

            # Delete all interactions for this session
            for interaction_id in interaction_ids:
                interaction_key = self._get_interaction_key(session_id, interaction_id)
                self.redis.delete(interaction_key)

            # Delete session key
            self.redis.delete(session_key)

            logger.info(f"Cleared Redis memory for session {session_id}")

        except Exception as e:
            logger.error(f"Error clearing session from Redis: {e}")

    async def clear_session_async(self, session_id: str):
        """Clear conversation history for a specific session (async)"""
        return await asyncio.to_thread(self.clear_session, session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if not self.redis_available:
            return {
                "enabled": Config.MEMORY_ENABLED,
                "redis_available": False,
                "error": "Redis not available",
            }

        try:
            # Count sessions
            session_pattern = self._get_session_key("*")
            sessions = self.redis.keys(session_pattern)
            total_sessions = len(sessions)

            # Count total interactions
            total_interactions = 0
            for session_key in sessions:
                session_id = session_key.replace("conversation:", "")
                interaction_count = self.redis.llen(session_key)
                total_interactions += interaction_count

            return {
                "enabled": Config.MEMORY_ENABLED,
                "redis_available": True,
                "total_sessions": total_sessions,
                "total_interactions": total_interactions,
                "max_entries": self.max_entries,
                "ttl_hours": self.ttl_seconds / 3600,
                "redis_url": self.redis_url,
            }

        except Exception as e:
            logger.error(f"Error getting Redis memory stats: {e}")
            return {
                "enabled": Config.MEMORY_ENABLED,
                "redis_available": True,
                "error": str(e),
            }

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory usage statistics (async)"""
        return await asyncio.to_thread(self.get_memory_stats)

    def cleanup_expired_sessions(self):
        """Clean up expired sessions and interactions"""
        if not self.redis_available:
            return

        try:
            # This is handled automatically by Redis TTL
            # But we can add additional cleanup logic here if needed
            logger.info("Redis TTL handles automatic cleanup of expired sessions")

        except Exception as e:
            logger.error(f"Error during Redis cleanup: {e}")

    def get_redis_health(self) -> Dict[str, Any]:
        """Get Redis connection health status"""
        if not self.redis_available:
            return {"available": False, "error": "Redis not initialized"}

        try:
            # Test connection
            self.redis.ping()
            return {
                "available": True,
                "url": self.redis_url,
                "ttl_seconds": self.ttl_seconds,
            }
        except Exception as e:
            return {"available": False, "error": str(e), "url": self.redis_url}


class LangChainConversationMemory:
    """
    LangChain-based conversation memory using ConversationBufferMemory with session ID support
    """

    def __init__(
        self,
        max_entries: int = Config.MEMORY_MAX_ENTRIES,
        max_age_hours: int = Config.MEMORY_MAX_AGE_HOURS,
    ):
        self.max_entries = max_entries
        self.max_age_seconds = max_age_hours * 3600
        self.sessions: Dict[str, ConversationBufferMemory] = {}
        self.session_timestamps: Dict[str, float] = {}

        if not LANGCHAIN_AVAILABLE:
            logger.warning(
                "LangChain not available, using fallback memory implementation"
            )

        logger.info(
            f"Initialized LangChain conversation memory with max_entries={max_entries}, max_age_hours={max_age_hours}"
        )

    def _get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create a ConversationBufferMemory for a session"""
        if session_id not in self.sessions:
            try:
                self.sessions[session_id] = ConversationBufferMemory(
                    return_messages=True, memory_key="chat_history"
                )
                self.session_timestamps[session_id] = time.time()
                logger.info(f"Created new LangChain memory for session {session_id}")
            except Exception as e:
                logger.error(
                    f"Failed to create LangChain memory for session {session_id}: {e}"
                )
                # Create a fallback memory object
                self.sessions[session_id] = ConversationBufferMemory()
                self.session_timestamps[session_id] = time.time()

        # Update timestamp
        self.session_timestamps[session_id] = time.time()
        return self.sessions[session_id]

    def _cleanup_old_sessions(self):
        """Remove sessions that have exceeded max age"""
        current_time = time.time()
        sessions_to_remove = []

        for session_id, timestamp in self.session_timestamps.items():
            if current_time - timestamp > self.max_age_seconds:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            del self.session_timestamps[session_id]
            logger.info(f"Cleaned up old session: {session_id}")

    def add_interaction(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",  # Keep parameter for backward compatibility but don't store
        metadata: Dict[str, Any] = None,
    ):
        """Add a new interaction to the conversation memory"""
        if not Config.MEMORY_ENABLED:
            return

        try:
            memory = self._get_or_create_memory(session_id)

            # Create LangChain messages (only store question and answer)
            human_message = HumanMessage(content=question)
            ai_message = AIMessage(content=answer)

            # Add messages to memory
            memory.chat_memory.add_user_message(question)
            memory.chat_memory.add_ai_message(answer)

            # Cleanup old sessions
            self._cleanup_old_sessions()

            logger.info(
                f"Added interaction to LangChain memory for session {session_id}"
            )

        except Exception as e:
            logger.error(f"Error adding interaction to LangChain memory: {e}")

    async def add_interaction_async(
        self,
        session_id: str,
        question: str,
        answer: str,
        context: str = "",
        metadata: Dict[str, Any] = None,
    ):
        """Add an interaction to the conversation memory (async)"""
        return await asyncio.to_thread(
            self.add_interaction, session_id, question, answer, context, metadata
        )

    def get_recent_context(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context for a session"""
        if not Config.MEMORY_ENABLED:
            return []

        try:
            memory = self._get_or_create_memory(session_id)
            messages = memory.chat_memory.messages

            # Convert LangChain messages to our format
            context_entries = []
            for i, message in enumerate(
                messages[-max_entries * 2 :], 1
            ):  # *2 because each interaction has 2 messages
                if isinstance(message, HumanMessage):
                    context_entries.append(
                        {
                            "id": f"{session_id}_{i}",
                            "timestamp": time.time(),
                            "question": message.content,
                            "answer": "",  # Will be filled by next message
                            "context": "",
                            "metadata": {},
                        }
                    )
                elif isinstance(message, AIMessage) and context_entries:
                    # Update the last entry with the answer
                    context_entries[-1]["answer"] = message.content

            return context_entries

        except Exception as e:
            logger.error(f"Error getting recent context from LangChain memory: {e}")
            return []

    async def get_recent_context_async(
        self, session_id: str, max_entries: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context for a session (async)"""
        return await asyncio.to_thread(self.get_recent_context, session_id, max_entries)

    def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation history"""
        if not Config.MEMORY_ENABLED:
            return ""

        try:
            memory = self._get_or_create_memory(session_id)
            messages = memory.chat_memory.messages

            if not messages:
                return ""

            # Create a simple summary of the conversation
            summary_parts = []
            for i, message in enumerate(messages):
                if isinstance(message, HumanMessage):
                    summary_parts.append(f"User: {message.content}")
                elif isinstance(message, AIMessage):
                    summary_parts.append(f"Assistant: {message.content}")

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(
                f"Error getting conversation summary from LangChain memory: {e}"
            )
            return ""

    async def get_conversation_summary_async(self, session_id: str) -> str:
        """Get a summary of the conversation history (async)"""
        return await asyncio.to_thread(self.get_conversation_summary, session_id)

    def clear_session(self, session_id: str):
        """Clear conversation history for a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            del self.session_timestamps[session_id]
            logger.info(f"Cleared LangChain memory for session {session_id}")

    async def clear_session_async(self, session_id: str):
        """Clear conversation history for a specific session (async)"""
        return await asyncio.to_thread(self.clear_session, session_id)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            total_sessions = len(self.sessions)
            total_interactions = sum(
                len(memory.chat_memory.messages) // 2
                for memory in self.sessions.values()
            )

            return {
                "enabled": Config.MEMORY_ENABLED,
                "type": "langchain_conversation_buffer",
                "total_sessions": total_sessions,
                "total_interactions": total_interactions,
                "max_entries": self.max_entries,
                "max_age_hours": self.max_age_seconds / 3600,
                "available": True,
            }
        except Exception as e:
            return {
                "enabled": Config.MEMORY_ENABLED,
                "type": "langchain_conversation_buffer",
                "error": str(e),
                "available": False,
            }

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory usage statistics (async)"""
        return await asyncio.to_thread(self.get_memory_stats)


def format_field_value(field_name: str, value: Any) -> str:
    """
    Format field values based on their type and content.
    """
    try:
        if value is None:
            return ""

        # Handle different data types
        if isinstance(value, (list, tuple)):
            if len(value) == 0:
                return ""
            else:
                # Show all items - no truncation
                return "; ".join(str(item) for item in value if item)

        elif isinstance(value, dict):
            # For dictionaries, show all key-value pairs - no truncation
            return "; ".join(f"{k}: {v}" for k, v in value.items() if v is not None)

        elif isinstance(value, str):
            # No truncation - return complete string
            return value

        elif isinstance(value, (int, float)):
            # Format numbers appropriately
            if field_name.lower() in ["price", "cost", "amount"] and isinstance(
                value, (int, float)
            ):
                return f"${value:.2f}" if value > 0 else str(value)
            elif field_name.lower() in ["rating", "score"] and isinstance(
                value, (int, float)
            ):
                return f"{value:.1f}" if 0 <= value <= 5 else str(value)
            else:
                return str(value)

        else:
            # For any other type, convert to string
            str_value = str(value)
            return str_value  # No truncation - return complete string

    except Exception as e:
        logger.warning(f"Error formatting field {field_name}: {e}")
        return str(value) if value else ""


def format_retrieved_context(documents: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents into a structured context string.
    """
    if not documents:
        logger.warning("No documents provided for context formatting")
        return "No relevant context found."

    context_parts = []

    # Define priority fields that should appear first if available
    priority_fields = [
        "title",
        "asin",
        "product_name",
        "name",
        "price",
        "rating",
        "average_rating",
        "main_category",
        "category",
        "description",
        "features",
    ]

    # Fields to skip or handle specially
    skip_fields = [
        "id",
        "vector",
        "embedding",
        "_id",
        "_search_vector",
        "_search_score",
        "_weighted_score",
        "_search_vectors",
        "_original_scores",
        "_best_score",
        "asin",
        "content_type",
        "doc_id",
        "source",
    ]

    # Content fields that contain the actual text that was embedded
    content_fields = [
        "_relevant_content",
        "page_content",
        "content",
        "text",
        "title_content",
        "review_content",
        "qa_content",
    ]

    # Also check for our canonical fields
    vector_content_fields = [
        ("title", ["title", "title_content", "page_content"]),
        ("reviews", ["reviews", "review_content"]),
        ("qa", ["qa", "qa_content"]),
    ]

    for i, doc in enumerate(documents, 1):
        try:
            doc_lines = [f"Document {i}:"]

            # Handle both Document objects and dictionaries
            if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                # It's a Document object
                doc_content = doc.page_content
                doc_metadata = doc.metadata
            else:
                # It's a dictionary
                doc_content = doc.get("page_content", "")
                doc_metadata = doc

            # Add search metadata if available
            search_info = []
            if "_search_vector" in doc_metadata:
                search_info.append(f"Found via: {doc_metadata['_search_vector']}")
            if "_search_score" in doc_metadata:
                search_info.append(f"Score: {doc_metadata['_search_score']:.3f}")
            if (
                "_search_vectors" in doc_metadata
                and len(doc_metadata["_search_vectors"]) > 1
            ):
                search_info.append(
                    f"Found in: {', '.join(doc_metadata['_search_vectors'])}"
                )

            if search_info:
                doc_lines.append(f"  Search Info: {' | '.join(search_info)}")

            # Add the main content
            if doc_content:
                doc_lines.append(f"  Content: {doc_content}")

            # Add metadata fields
            for key, value in doc_metadata.items():
                if (
                    key.lower() not in skip_fields
                    and not key.startswith("_vector_")
                    and value is not None
                    and key not in ["page_content"]
                ):  # Skip page_content as we already showed it
                    formatted_value = format_field_value(key, value)
                    if formatted_value:
                        doc_lines.append(
                            f"  {key.replace('_', ' ').title()}: {formatted_value}"
                        )

            context_parts.append("\n".join(doc_lines))

        except Exception as e:
            logger.error(f"Error formatting document {i}: {e}")
            # Fallback: show basic document info
            try:
                if hasattr(doc, "page_content"):
                    context_parts.append(f"Document {i}: {doc.page_content[:200]}...")
                else:
                    context_parts.append(f"Document {i}: {str(doc)[:200]}...")
            except:
                context_parts.append(f"Document {i}: Error formatting document data")

    formatted_context = "\n\n".join(context_parts)

    # No truncation - return complete context
    logger.info(
        f"Formatted complete context from {len(documents)} documents ({len(formatted_context)} characters)"
    )

    logger.info(f"Formatted context from {len(documents)} documents")
    return formatted_context


async def format_retrieved_context_async(documents: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents into a structured context string (async).
    """
    return await asyncio.to_thread(format_retrieved_context, documents)


# Business Logic Functions for RAG Pipeline


def retrieve_context_sync(
    retriever, query: str, top_k: int = None, retrieval_method: str = "multi"
) -> str:
    """
    Retrieve relevant context for a given query using different retrieval methods (sync).
    """
    if top_k is None:
        top_k = Config.TOP_K_RETRIEVAL

    logger.info(
        f"Retrieving context for query: '{query}' (method={retrieval_method}, top_k={top_k})"
    )

    try:
        # Choose retrieval method
        if retrieval_method == "title_first":
            try:
                result = retriever.title_first_search(
                    query, top_products=top_k, items_per_product=3
                )
                # Defensive check for result
                if result is None:
                    logger.warning("title_first_search returned None")
                    return "No relevant products found."

                # Use the new product-based formatting
                if result.get("results"):
                    formatted_context = retriever.format_product_data_for_llm(
                        result["results"]
                    )
                    return formatted_context
                else:
                    return "No relevant products found."
            except Exception as e:
                logger.error(f"Error in title_first_search: {e}")
                return "Error occurred while searching for products."
        elif retrieval_method == "title":
            retrieved_docs = retriever.search_titles(query, k=top_k)
        elif retrieval_method == "reviews":
            retrieved_docs = retriever.search_reviews(query, k=top_k)
        elif retrieval_method == "qa":
            retrieved_docs = retriever.search_qas(query, k=top_k)
        else:  # default to "multi" - search all types
            # Combine results from all types
            title_docs = retriever.search_titles(query, k=top_k // 3)
            review_docs = retriever.search_reviews(query, k=top_k // 3)
            qa_docs = retriever.search_qas(query, k=top_k // 3)
            retrieved_docs = title_docs + review_docs + qa_docs

        if not retrieved_docs:
            logger.warning("No documents retrieved from vector database")
            return "No relevant information found in the database."

        logger.info(
            f"Successfully retrieved {len(retrieved_docs)} documents using {retrieval_method} method"
        )

        # Format the retrieved documents
        formatted_context = format_retrieved_context(retrieved_docs)
        return formatted_context

    except Exception as e:
        logger.error(f"Error during context retrieval: {e}")
        return "Error occurred while retrieving relevant information."


async def retrieve_context_async(
    retriever, query: str, top_k: int = None, retrieval_method: str = "multi"
) -> str:
    """
    Retrieve relevant context for a given query using different retrieval methods (async).
    """
    if top_k is None:
        top_k = Config.TOP_K_RETRIEVAL

    logger.info(
        f"Retrieving context for query: '{query}' (method={retrieval_method}, top_k={top_k})"
    )

    try:
        # Choose retrieval method
        if retrieval_method == "title_first":
            try:
                result = await retriever.title_first_search_async(
                    query, top_products=top_k, items_per_product=3
                )
                # Defensive check for result
                if result is None:
                    logger.warning("title_first_search_async returned None")
                    return "No relevant products found."

                # Use the new product-based formatting
                if result.get("results"):
                    formatted_context = (
                        await retriever.format_product_data_for_llm_async(
                            result["results"]
                        )
                    )
                    return formatted_context
                else:
                    return "No relevant products found."
            except Exception as e:
                logger.error(f"Error in title_first_search_async: {e}")
                return "Error occurred while searching for products."
        elif retrieval_method == "title":
            retrieved_docs = await retriever.search_titles_async(query, k=top_k)
        elif retrieval_method == "reviews":
            retrieved_docs = await retriever.search_reviews_async(query, k=top_k)
        elif retrieval_method == "qa":
            retrieved_docs = await retriever.search_qas_async(query, k=top_k)
        else:  # default to "multi" - search all types
            # Combine results from all types
            title_docs = await retriever.search_titles_async(query, k=top_k // 3)
            review_docs = await retriever.search_reviews_async(query, k=top_k // 3)
            qa_docs = await retriever.search_qas_async(query, k=top_k // 3)
            retrieved_docs = title_docs + review_docs + qa_docs

        if not retrieved_docs:
            logger.warning("No documents retrieved from vector database")
            return "No relevant information found in the database."

        logger.info(
            f"Successfully retrieved {len(retrieved_docs)} documents using {retrieval_method} method"
        )

        # Format the retrieved documents
        formatted_context = await format_retrieved_context_async(retrieved_docs)
        return formatted_context

    except Exception as e:
        logger.error(f"Error during context retrieval: {e}")
        return "Error occurred while retrieving relevant information."


def generate_answer_sync(
    llm_client,
    context: str,
    question: str,
    session_id: str = None,
    conversation_history: str = "",
) -> str:
    """
    Generate an answer using the Groq API with retrieved context and conversation memory (synchronous).
    """
    logger.info(f"Generating answer for question: '{question}' (session: {session_id})")

    try:
        # Get system prompt from centralized prompts module
        system_prompt = get_rag_system_prompt()

        # Build user prompt using centralized function
        user_prompt = build_rag_user_prompt(context, question, conversation_history)

        # Prepare messages for the chat completion
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info("Sending request to Groq API")

        # Generate response using robust LLM client
        response = llm_client.generate_response(
            messages,
            temperature=0.1,  # Lower temperature for more consistent responses
            max_tokens=1024,
            top_p=0.9,
            stream=False,
            stop=None,
        )

        # Extract the generated answer
        answer = response

        logger.info("Successfully generated answer from Groq API")
        logger.debug(f"Generated answer length: {len(answer)} characters")

        return answer

    except Exception as e:
        logger.error(f"Error during answer generation: {e}")
        return f"I apologize, but I encountered an error while generating an answer. Please try again later. Error: {str(e)}"


async def generate_answer_async(
    llm_client,
    context: str,
    question: str,
    session_id: str = None,
    conversation_history: str = "",
) -> str:
    """
    Generate an answer using the Groq API with retrieved context and conversation memory (async).
    """
    logger.info(f"Generating answer for question: '{question}' (session: {session_id})")

    try:
        # Get system prompt from centralized prompts module
        system_prompt = get_rag_system_prompt()

        # Build user prompt using centralized function
        user_prompt = build_rag_user_prompt(context, question, conversation_history)

        # Prepare messages for the chat completion
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info("Sending request to Groq API")

        # Generate response using robust LLM client
        response = await llm_client.generate_response_async(messages)
        logger.info(f"Generated response: {len(response)} characters")

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise

    # Store in memory if enabled
    if memory_enabled and session_id and memory:
        try:
            await memory.add_interaction_async(
                session_id=session_id,
                question=question,
                answer=answer,
                context=context,
                metadata={
                    "retrieval_performed": metadata["retrieval_performed"],
                    "conversation_only_mode": metadata["conversation_only_mode"],
                    "retrieval_method": retrieval_method,
                    "model_used": model,
                },
            )
            logger.info(f"Added interaction to memory for session {session_id}")
        except Exception as e:
            logger.warning(f"Error storing in memory: {e}")

    return {
        "question": question,
        "answer": answer,
        "context": context,
        "conversation_history": conversation_history,
        "metadata": metadata,
    }


def run_rag_pipeline_sync(
    retriever,
    llm_client,
    memory,
    memory_enabled: bool,
    model: str,
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "multi",
) -> Dict[str, Any]:
    """
    Complete RAG pipeline: retrieve context and generate answer with memory support (sync).
    """
    if top_k is None:
        top_k = Config.TOP_K_RETRIEVAL

    logger.info(
        f"Starting RAG pipeline for question: '{question}' (session: {session_id}, method={retrieval_method})"
    )

    try:
        # Step 1: Get conversation history if memory is enabled
        conversation_history = ""
        if memory_enabled and session_id and memory:
            conversation_history = memory.get_conversation_summary(session_id)
            logger.info(f"Retrieved conversation history for session {session_id}")

        # Step 2: Retrieve relevant context
        logger.info("Step 2: Retrieving context...")
        context = retrieve_context_sync(
            retriever, question, top_k=top_k, retrieval_method=retrieval_method
        )

        # Step 3: Generate answer with conversation history
        logger.info("Step 3: Generating answer...")
        answer = generate_answer_sync(
            llm_client, context, question, session_id, conversation_history
        )

        # Log comprehensive token breakdown for sync version
        from prompts import get_rag_system_prompt
        system_prompt = get_rag_system_prompt()
        
        query_data = {
            "user_prompt": question,
            "system_prompt": system_prompt,
            "conversation_history": conversation_history,
            "retrieved_context": context,
            "llm_response": answer
        }
        
        log_comprehensive_token_breakdown(session_id, query_data)

        # Step 4: Store interaction in memory if enabled
        if memory_enabled and session_id and memory:
            memory.add_interaction(
                session_id=session_id,
                question=question,
                answer=answer,
                context=context,
                metadata={
                    "top_k_used": top_k,
                    "retrieval_method": retrieval_method,
                    "model_used": model,
                },
            )

        # Prepare result
        result = {
            "question": question,
            "answer": answer,
            "context": context,
            "conversation_history": conversation_history,
            "session_id": session_id,
            "metadata": {
                "top_k_used": top_k,
                "retrieval_method": retrieval_method,
                "model_used": model,
                "context_length": len(context),
                "answer_length": len(answer),
                "memory_enabled": memory_enabled,
                "has_conversation_history": bool(conversation_history),
            },
        }

        logger.info("RAG pipeline completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
        return {
            "question": question,
            "context": "",
            "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}",
            "metadata": {
                "error": str(e),
                "top_k_used": top_k,
                "retrieval_method": retrieval_method,
                "model_used": model,
            },
        }


async def run_rag_pipeline_async(
    retriever,
    llm_client,
    memory,
    memory_enabled: bool,
    model: str,
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "multi",
) -> Dict[str, Any]:
    """
    Complete RAG pipeline: retrieve context and generate answer with memory support (async).
    Implements intelligent retrieval logic that only retrieves new data when necessary.
    """
    from prompts import (
        should_retrieve_new_data,
        build_rag_user_prompt,
        get_rag_system_prompt,
        build_conversation_only_prompt,
        get_conversation_only_system_prompt,
    )

    pipeline_start_time = time.time()
    
    # Log pipeline start with rich logging
    log_pipeline_step("Pipeline Start", session_id, {
        "question_length": len(question),
        "memory_enabled": memory_enabled,
        "retrieval_method": retrieval_method,
        "model": model
    })
    
    logger.info("Starting RAG pipeline", extra={
        "component": "rag_pipeline",
        "operation": "run_rag_pipeline_async",
        "session_id": session_id,
        "question_length": len(question),
        "memory_enabled": memory_enabled,
        "retrieval_method": retrieval_method,
        "model": model
    })

    # Initialize metadata
    metadata = {
        "memory_enabled": memory_enabled,
        "session_id_provided": session_id is not None,
        "memory_object_available": memory is not None,
        "retrieval_method": retrieval_method,
        "model_used": model,
        "retrieval_performed": False,
        "conversation_only_mode": False,
    }

    # Get conversation history if memory is enabled
    conversation_history = ""
    has_conversation_history = False

    if memory_enabled and session_id and memory:
        try:
            conversation_start_time = time.time()
            conversation_history = await memory.get_conversation_summary_async(
                session_id
            )
            conversation_time = (time.time() - conversation_start_time) * 1000
            
            if conversation_history:
                has_conversation_history = True
                history_tokens = count_tokens(conversation_history)
                
                log_pipeline_step("Conversation History Retrieved", session_id, {
                    "conversation_length": len(conversation_history),
                    "history_tokens": history_tokens,
                    "processing_time_ms": conversation_time
                })
                
                logger.info("Retrieved conversation history", extra={
                    "component": "rag_pipeline",
                    "operation": "get_conversation_history",
                    "session_id": session_id,
                    "conversation_length": len(conversation_history),
                    "history_tokens": history_tokens,
                    "processing_time_ms": conversation_time,
                    "optimization": "context_excluded_from_history"
                })
            else:
                log_pipeline_step("No Conversation History", session_id, {
                    "processing_time_ms": conversation_time
                })
                logger.info("No conversation history found", extra={
                    "component": "rag_pipeline",
                    "operation": "get_conversation_history",
                    "session_id": session_id,
                    "processing_time_ms": conversation_time
                })
        except Exception as e:
            logger.warning("Error retrieving conversation history", extra={
                "component": "rag_pipeline",
                "operation": "get_conversation_history",
                "session_id": session_id,
                "error": str(e)
            })

    metadata["has_conversation_history"] = has_conversation_history
    metadata["conversation_history_length"] = len(conversation_history)

    # Determine if we need to retrieve new data using LangChain agent
    from rag.agent import RetrievalAgent

    agent_start_time = time.time()
    agent = RetrievalAgent(memory)
    should_retrieve = await agent.should_retrieve_new_data(question, session_id)
    agent_time = (time.time() - agent_start_time) * 1000
    
    # Log agent decision with rich logging
    log_agent_decision(session_id, "retrieve" if should_retrieve else "conversation", {
        "confidence": "high",
        "rationale": f"Agent decided to {'retrieve new data' if should_retrieve else 'use conversation history only'}"
    })
    
    logger.info("Agent decision made", extra={
        "component": "rag_pipeline",
        "operation": "agent_decision",
        "session_id": session_id,
        "should_retrieve": should_retrieve,
        "processing_time_ms": agent_time
    })

    # Track what will be sent to LLM
    prompt_components = {
        "content": {},
        "tokens": {}
    }

    if should_retrieve:
        # Full RAG mode: retrieve new data
        log_pipeline_step("Retrieving New Data", session_id, {
            "retrieval_method": retrieval_method
        })
        
        logger.info("Retrieving new data for question", extra={
            "component": "rag_pipeline",
            "operation": "retrieve_new_data",
            "session_id": session_id,
            "retrieval_method": retrieval_method
        })
        metadata["retrieval_performed"] = True
        metadata["conversation_only_mode"] = False

        # Retrieve context
        retrieval_start_time = time.time()
        context = await retrieve_context_async(
            retriever=retriever,
            query=question,
            top_k=top_k,
            retrieval_method=retrieval_method,
        )
        retrieval_time = (time.time() - retrieval_start_time) * 1000

        # Build RAG prompt with context
        system_prompt = get_rag_system_prompt()
        user_prompt = build_rag_user_prompt(
            context=context,
            question=question,
            conversation_history=conversation_history,
        )

        # Track prompt components
        prompt_components["content"] = {
            "system_prompt": system_prompt,
            "conversation_history": conversation_history,
            "retrieved_context": context,
            "user_question": question
        }
        
        prompt_components["tokens"] = {
            "system_prompt": count_tokens(system_prompt),
            "conversation_history": count_tokens(conversation_history),
            "retrieved_context": count_tokens(context),
            "user_question": count_tokens(question)
        }

        # Log what's being sent to LLM
        log_what_sent_to_llm(session_id, prompt_components)
        
        # Log prompt analysis
        log_prompt_analysis(session_id, {
            "conversation_only": False,
            "system_tokens": prompt_components["tokens"]["system_prompt"],
            "history_tokens": prompt_components["tokens"]["conversation_history"],
            "context_tokens": prompt_components["tokens"]["retrieved_context"],
            "question_tokens": prompt_components["tokens"]["user_question"],
            "system_content": system_prompt,
            "history_content": conversation_history,
            "context_content": context,
            "question_content": question,
            "savings_from_optimization": 0  # No savings in RAG mode
        })

        logger.info("Built RAG prompt with context", extra={
            "component": "rag_pipeline",
            "operation": "build_rag_prompt",
            "session_id": session_id,
            "context_length": len(context),
            "context_tokens": prompt_components["tokens"]["retrieved_context"],
            "conversation_history_length": len(conversation_history),
            "history_tokens": prompt_components["tokens"]["conversation_history"],
            "system_prompt_length": len(system_prompt),
            "system_tokens": prompt_components["tokens"]["system_prompt"],
            "user_prompt_length": len(user_prompt),
            "user_tokens": prompt_components["tokens"]["user_question"],
            "total_prompt_length": len(system_prompt) + len(user_prompt),
            "total_tokens": sum(prompt_components["tokens"].values()),
            "retrieval_time_ms": retrieval_time,
            "optimization": "context_only_for_current_prompt"
        })

    else:
        # Conversation-only mode: use existing conversation history
        log_pipeline_step("Using Conversation History Only", session_id, {
            "conversation_history_length": len(conversation_history)
        })
        
        logger.info("Using conversation history only - no new retrieval", extra={
            "component": "rag_pipeline",
            "operation": "conversation_only_mode",
            "session_id": session_id,
            "conversation_history_length": len(conversation_history)
        })
        metadata["retrieval_performed"] = False
        metadata["conversation_only_mode"] = True

        # Use conversation-only prompt
        system_prompt = get_conversation_only_system_prompt()
        user_prompt = build_conversation_only_prompt(
            question=question, conversation_history=conversation_history
        )

        # Track prompt components (no context in conversation-only mode)
        prompt_components["content"] = {
            "system_prompt": system_prompt,
            "conversation_history": conversation_history,
            "user_question": question
        }
        
        prompt_components["tokens"] = {
            "system_prompt": count_tokens(system_prompt),
            "conversation_history": count_tokens(conversation_history),
            "user_question": count_tokens(question)
        }

        # Log what's being sent to LLM
        log_what_sent_to_llm(session_id, prompt_components)
        
        # Log prompt analysis
        log_prompt_analysis(session_id, {
            "conversation_only": True,
            "system_tokens": prompt_components["tokens"]["system_prompt"],
            "history_tokens": prompt_components["tokens"]["conversation_history"],
            "context_tokens": 0,  # No context in conversation-only mode
            "question_tokens": prompt_components["tokens"]["user_question"],
            "system_content": system_prompt,
            "history_content": conversation_history,
            "question_content": question,
            "savings_from_optimization": 0  # No context to save
        })

        logger.info("Built conversation-only prompt", extra={
            "component": "rag_pipeline",
            "operation": "build_conversation_prompt",
            "session_id": session_id,
            "conversation_history_length": len(conversation_history),
            "history_tokens": prompt_components["tokens"]["conversation_history"],
            "system_prompt_length": len(system_prompt),
            "system_tokens": prompt_components["tokens"]["system_prompt"],
            "user_prompt_length": len(user_prompt),
            "user_tokens": prompt_components["tokens"]["user_question"],
            "total_prompt_length": len(system_prompt) + len(user_prompt),
            "total_tokens": sum(prompt_components["tokens"].values()),
            "optimization": "no_context_retrieval_needed"
        })

        # Set empty context for conversation-only mode
        context = ""

    # Generate answer
    generation_start_time = time.time()
    answer = await generate_answer_async(
        llm_client=llm_client,
        context=context,
        question=question,
        session_id=session_id,
        conversation_history=conversation_history,
    )
    generation_time = (time.time() - generation_start_time) * 1000

    # Count output tokens
    answer_tokens = count_tokens(answer)
    
    # Log comprehensive token breakdown
    query_data = {
        "user_prompt": question,
        "system_prompt": prompt_components["content"].get("system_prompt", ""),
        "conversation_history": conversation_history,
        "retrieved_context": context,
        "llm_response": answer
    }
    
    log_comprehensive_token_breakdown(session_id, query_data)
    
    log_pipeline_step("Generated Answer", session_id, {
        "answer_length": len(answer),
        "answer_tokens": answer_tokens,
        "generation_time_ms": generation_time
    })

    logger.info("Generated answer", extra={
        "component": "rag_pipeline",
        "operation": "generate_answer",
        "session_id": session_id,
        "answer_length": len(answer),
        "answer_tokens": answer_tokens,
        "generation_time_ms": generation_time
    })

    # Store interaction in memory if enabled
    if memory_enabled and session_id and memory:
        try:
            memory_start_time = time.time()
            await memory.add_interaction_async(
                session_id=session_id,
                question=question,
                answer=answer,
                context=context,
                metadata={
                    "retrieval_performed": metadata["retrieval_performed"],
                    "conversation_only_mode": metadata["conversation_only_mode"],
                    "retrieval_method": retrieval_method,
                    "model_used": model,
                },
            )
            memory_time = (time.time() - memory_start_time) * 1000
            
            # Log memory operation with rich logging
            log_memory_operation("Add Interaction", session_id, {
                "context_length": len(context),
                "interaction_size_bytes": len(json.dumps({
                    "question": question,
                    "answer": answer,
                    "metadata": metadata
                })),
                "processing_time_ms": memory_time
            })
            
            logger.info("Stored interaction in memory", extra={
                "component": "rag_pipeline",
                "operation": "store_interaction",
                "session_id": session_id,
                "processing_time_ms": memory_time,
                "optimization": "context_not_stored_in_memory"
            })
        except Exception as e:
            logger.warning("Error storing interaction in memory", extra={
                "component": "rag_pipeline",
                "operation": "store_interaction",
                "session_id": session_id,
                "error": str(e)
            })

    # Prepare final result
    result = {
        "question": question,
        "answer": answer,
        "context": context,
        "conversation_history": conversation_history,
        "metadata": metadata,
    }

    total_time = (time.time() - pipeline_start_time) * 1000
    
    # Log final summary with rich logging
    summary_data = {
        "total_time_ms": total_time,
        "retrieval_performed": metadata["retrieval_performed"],
        "conversation_only_mode": metadata["conversation_only_mode"],
        "input_tokens": sum(prompt_components["tokens"].values()),
        "output_tokens": answer_tokens,
        "context_tokens": prompt_components["tokens"].get("retrieved_context", 0),
        "history_tokens": prompt_components["tokens"].get("conversation_history", 0),
        "system_tokens": prompt_components["tokens"].get("system_prompt", 0),
        "question_tokens": prompt_components["tokens"].get("user_question", 0)
    }
    
    log_final_summary(session_id, summary_data)
    
    logger.info("RAG pipeline completed", extra={
        "component": "rag_pipeline",
        "operation": "complete",
        "session_id": session_id,
        "total_time_ms": total_time,
        "retrieval_performed": metadata["retrieval_performed"],
        "conversation_only_mode": metadata["conversation_only_mode"],
        "input_tokens": summary_data["input_tokens"],
        "output_tokens": summary_data["output_tokens"],
        "context_optimization": "enabled"
    })

    return result


def get_system_health_sync(
    memory, memory_enabled: bool, model: str, retriever, llm_client
) -> Dict[str, Any]:
    """Get comprehensive system health status (sync)"""
    memory_stats = (
        memory.get_memory_stats()
        if memory
        else {"enabled": False, "error": "Memory not initialized"}
    )

    # Add Redis health if using Redis memory
    redis_health = None
    if (
        memory
        and hasattr(memory, "get_redis_health")
        and isinstance(memory, RedisConversationMemory)
    ):
        redis_health = memory.get_redis_health()

    return {
        "llm_client": (
            llm_client.get_health_status()
            if llm_client
            else {"error": "LLM client not initialized"}
        ),
        "memory": memory_stats,
        "redis_health": redis_health,
        "retriever_available": retriever is not None,
        "memory_enabled": memory_enabled,
        "model": model,
    }


async def get_system_health_async(
    memory, memory_enabled: bool, model: str, retriever, llm_client
) -> Dict[str, Any]:
    """Get comprehensive system health status (async)"""
    memory_stats = (
        await memory.get_memory_stats_async()
        if memory
        else {"enabled": False, "error": "Memory not initialized"}
    )

    # Add Redis health if using Redis memory
    redis_health = None
    if (
        memory
        and hasattr(memory, "get_redis_health")
        and isinstance(memory, RedisConversationMemory)
    ):
        redis_health = await memory.get_redis_health_async()

    return {
        "llm_client": (
            await llm_client.get_health_status_async()
            if llm_client
            else {"error": "LLM client not initialized"}
        ),
        "memory": memory_stats,
        "redis_health": redis_health,
        "retriever_available": retriever is not None,
        "memory_enabled": memory_enabled,
        "model": model,
    }
