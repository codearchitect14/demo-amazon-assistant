"""
LLM client implementation for interacting with language models.
"""

import logging
import time
import random
from typing import List, Dict, Any, Optional
from groq import Groq, AsyncGroq
# Import config conditionally to avoid circular imports
try:
    from app.config import Config
except ImportError:
    # Fallback configuration if app.config is not available
    class Config:
        CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
        CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
        RETRY_MAX_ATTEMPTS = 3
        RETRY_BASE_DELAY = 1.0
        RETRY_MAX_DELAY = 10.0

from rag.resilience.circuit_breaker import CircuitBreaker
from rag.resilience.retry_handler import RetryHandler
from shared.utils.serialization import serialize_for_json

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM client with circuit breaker and retry logic for resilient operation.
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
        """
        Initialize LLM client.
        
        Args:
            primary_api_key: Primary API key for LLM service
            primary_model: Primary model to use
            fallback_api_key: Fallback API key for LLM service
            fallback_model: Fallback model to use
            enable_circuit_breaker: Whether to enable circuit breaker
            enable_retry: Whether to enable retry logic
        """
        self.primary_api_key = primary_api_key
        self.primary_model = primary_model
        self.fallback_api_key = fallback_api_key
        self.fallback_model = fallback_model
        
        # Initialize clients
        self.primary_client = Groq(api_key=primary_api_key)
        self.primary_async_client = AsyncGroq(api_key=primary_api_key)
        
        if fallback_api_key:
            self.fallback_client = Groq(api_key=fallback_api_key)
            self.fallback_async_client = AsyncGroq(api_key=fallback_api_key)
        else:
            self.fallback_client = None
            self.fallback_async_client = None

        # Initialize resilience components
        if enable_circuit_breaker:
            self.primary_circuit_breaker = CircuitBreaker(
                failure_threshold=Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                recovery_timeout=Config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            )
            if fallback_api_key:
                self.fallback_circuit_breaker = CircuitBreaker(
                    failure_threshold=Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                    recovery_timeout=Config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                )
        else:
            self.primary_circuit_breaker = None
            self.fallback_circuit_breaker = None

        if enable_retry:
            self.retry_handler = RetryHandler(
                max_retries=Config.RETRY_MAX_ATTEMPTS,
                base_delay=Config.RETRY_BASE_DELAY,
                max_delay=Config.RETRY_MAX_DELAY,
            )
        else:
            self.retry_handler = None

        # Health tracking
        self.primary_health = {
            "success_count": 0,
            "failure_count": 0,
            "last_success": None,
            "last_failure": None,
            "average_response_time": 0.0,
        }
        
        if fallback_api_key:
            self.fallback_health = {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None,
                "average_response_time": 0.0,
            }

        logger.info(f"LLM client initialized with primary model: {primary_model}")

    def _make_request(
        self, client: Groq, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """
        Make synchronous request to LLM.
        
        Args:
            client: Groq client instance
            model: Model to use
            messages: Messages to send
            **kwargs: Additional arguments
            
        Returns:
            Response from LLM
        """
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def _make_request_async(
        self, client: AsyncGroq, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """
        Make asynchronous request to LLM.
        
        Args:
            client: AsyncGroq client instance
            model: Model to use
            messages: Messages to send
            **kwargs: Additional arguments
            
        Returns:
            Response from LLM
        """
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Async LLM request failed: {e}")
            raise

    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate response using primary model with fallback.
        
        Args:
            messages: Messages to send
            **kwargs: Additional arguments
            
        Returns:
            Response from LLM
        """
        start_time = time.time()
        
        try:
            # Try primary model
            if self.primary_circuit_breaker:
                result = self.primary_circuit_breaker.call(
                    self._make_request,
                    self.primary_client,
                    self.primary_model,
                    messages,
                    **kwargs
                )
            else:
                result = self._make_request(
                    self.primary_client,
                    self.primary_model,
                    messages,
                    **kwargs
                )
            
            # Update health metrics
            response_time = time.time() - start_time
            self._update_health_metrics(self.primary_health, True, response_time)
            
            return result
            
        except Exception as e:
            logger.warning(f"Primary model failed: {e}")
            self._update_health_metrics(self.primary_health, False, time.time() - start_time)
            
            # Try fallback if available
            if self.fallback_client and self.fallback_api_key:
                try:
                    if self.fallback_circuit_breaker:
                        result = self.fallback_circuit_breaker.call(
                            self._make_request,
                            self.fallback_client,
                            self.fallback_model,
                            messages,
                            **kwargs
                        )
                    else:
                        result = self._make_request(
                            self.fallback_client,
                            self.fallback_model,
                            messages,
                            **kwargs
                        )
                    
                    self._update_health_metrics(self.fallback_health, True, time.time() - start_time)
                    logger.info("Used fallback model successfully")
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    self._update_health_metrics(self.fallback_health, False, time.time() - start_time)
                    raise
            
            raise

    async def generate_response_async(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """
        Generate response asynchronously using primary model with fallback.
        
        Args:
            messages: Messages to send
            **kwargs: Additional arguments
            
        Returns:
            Response from LLM
        """
        start_time = time.time()
        
        try:
            # Try primary model
            if self.primary_circuit_breaker:
                result = await self.primary_circuit_breaker.call_async(
                    self._make_request_async,
                    self.primary_async_client,
                    self.primary_model,
                    messages,
                    **kwargs
                )
            else:
                result = await self._make_request_async(
                    self.primary_async_client,
                    self.primary_model,
                    messages,
                    **kwargs
                )
            
            # Update health metrics
            response_time = time.time() - start_time
            self._update_health_metrics(self.primary_health, True, response_time)
            
            return result
            
        except Exception as e:
            logger.warning(f"Primary model failed: {e}")
            self._update_health_metrics(self.primary_health, False, time.time() - start_time)
            
            # Try fallback if available
            if self.fallback_async_client and self.fallback_api_key:
                try:
                    if self.fallback_circuit_breaker:
                        result = await self.fallback_circuit_breaker.call_async(
                            self._make_request_async,
                            self.fallback_async_client,
                            self.fallback_model,
                            messages,
                            **kwargs
                        )
                    else:
                        result = await self._make_request_async(
                            self.fallback_async_client,
                            self.fallback_model,
                            messages,
                            **kwargs
                        )
                    
                    self._update_health_metrics(self.fallback_health, True, time.time() - start_time)
                    logger.info("Used fallback model successfully")
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    self._update_health_metrics(self.fallback_health, False, time.time() - start_time)
                    raise
            
            raise

    async def generate_response_stream_async(
        self, messages: List[Dict[str, str]], **kwargs
    ):
        """
        Generate streaming response asynchronously.
        
        Args:
            messages: Messages to send
            **kwargs: Additional arguments
            
        Yields:
            Streaming response chunks
        """
        try:
            # Try primary model (without circuit breaker for streaming)
            async for chunk in self._make_streaming_request_async(
                self.primary_async_client,
                self.primary_model,
                messages,
                **kwargs
            ):
                yield chunk
                    
        except Exception as e:
            logger.warning(f"Primary model streaming failed: {e}")
            
            # Try fallback if available
            if self.fallback_async_client and self.fallback_model and self.fallback_api_key:
                logger.info(f"Attempting fallback to model: {self.fallback_model}")
                try:
                    async for chunk in self._make_streaming_request_async(
                        self.fallback_async_client,
                        self.fallback_model,
                        messages,
                        **kwargs
                    ):
                        yield chunk
                    
                    logger.info("Successfully used fallback model")
                    return
                            
                except Exception as fallback_error:
                    logger.error(f"Fallback model streaming also failed: {fallback_error}")
                    raise
            else:
                logger.warning("No fallback model available - skipping fallback attempt")
            
            raise

    async def _make_streaming_request_async(
        self, client: AsyncGroq, model: str, messages: List[Dict[str, str]], **kwargs
    ):
        """
        Make streaming request to LLM.
        
        Args:
            client: AsyncGroq client instance
            model: Model to use
            messages: Messages to send
            **kwargs: Additional arguments
            
        Yields:
            Streaming response chunks
        """
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming LLM request failed: {e}")
            raise

    def _update_health_metrics(self, health_dict: Dict[str, Any], success: bool, response_time: float):
        """Update health metrics for a model."""
        if success:
            health_dict["success_count"] += 1
            health_dict["last_success"] = time.time()
            
            # Update average response time
            current_avg = health_dict["average_response_time"]
            count = health_dict["success_count"]
            health_dict["average_response_time"] = (current_avg * (count - 1) + response_time) / count
        else:
            health_dict["failure_count"] += 1
            health_dict["last_failure"] = time.time()

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of LLM clients.
        
        Returns:
            Dictionary with health information
        """
        health_status = {
            "primary": serialize_for_json(self.primary_health),
            "primary_circuit_breaker": (
                self.primary_circuit_breaker.get_state() 
                if self.primary_circuit_breaker else None
            ),
        }
        
        if self.fallback_api_key:
            health_status["fallback"] = serialize_for_json(self.fallback_health)
            health_status["fallback_circuit_breaker"] = (
                self.fallback_circuit_breaker.get_state() 
                if self.fallback_circuit_breaker else None
            )
        
        return health_status

    async def get_health_status_async(self) -> Dict[str, Any]:
        """
        Get health status asynchronously.
        
        Returns:
            Dictionary with health information
        """
        return self.get_health_status()

    def reset_health(self):
        """Reset health metrics."""
        self.primary_health = {
            "success_count": 0,
            "failure_count": 0,
            "last_success": None,
            "last_failure": None,
            "average_response_time": 0.0,
        }
        
        if self.fallback_api_key:
            self.fallback_health = {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None,
                "average_response_time": 0.0,
            }
        
        if self.primary_circuit_breaker:
            self.primary_circuit_breaker.reset()
        
        if self.fallback_circuit_breaker:
            self.fallback_circuit_breaker.reset()
        
        logger.info("LLM client health metrics reset") 