"""
API abstraction layer to decouple frontend from API implementation.
"""

import logging
import aiohttp
import json
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from shared.utils.error_handling import NetworkError, ValidationError
from shared.utils.validation import DataSanitizer

logger = logging.getLogger(__name__)


class APIClientInterface(ABC):
    """Abstract API client interface."""
    
    @abstractmethod
    async def make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request."""
        pass
    
    @abstractmethod
    async def make_streaming_request(self, endpoint: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Make streaming API request."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close client resources."""
        pass


class APIClient(APIClientInterface):
    """Concrete API client implementation with proper session management."""
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip('/')
        self.sanitizer = DataSanitizer()
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # Log initialization
        logger.info("APIClient initialized", extra={
            "component": "api_client",
            "operation": "init",
            "base_url": base_url
        })
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper locking."""
        async with self._session_lock:
            if self.session is None or self.session.closed:
                logger.info("Creating new aiohttp session", extra={
                    "component": "api_client",
                    "operation": "create_session"
                })
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
                )
            return self.session
    
    async def make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request with error handling and validation.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            API response
            
        Raises:
            NetworkError: If request fails
            ValidationError: If data is invalid
        """
        start_time = asyncio.get_event_loop().time()
        
        logger.info("Making API request", extra={
            "component": "api_client",
            "operation": "make_request",
            "endpoint": endpoint,
            "data_size": len(str(data))
        })
        
        try:
            # Sanitize and validate data
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = self.sanitizer.sanitize_string(value)
                else:
                    sanitized_data[key] = value
            
            session = await self._get_session()
            url = f"{self.base_url}{endpoint}"
            
            async with session.post(url, json=sanitized_data) as response:
                processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    logger.info("API request successful", extra={
                        "component": "api_client",
                        "operation": "make_request",
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "processing_time_ms": processing_time
                    })
                    return result
                else:
                    error_text = await response.text()
                    logger.error("API request failed", extra={
                        "component": "api_client",
                        "operation": "make_request",
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "error_text": error_text,
                        "processing_time_ms": processing_time
                    })
                    raise NetworkError(
                        f"API request failed with status {response.status}",
                        url=url,
                        status_code=response.status
                    )
                    
        except aiohttp.ClientError as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error("Network error in API request", extra={
                "component": "api_client",
                "operation": "make_request",
                "endpoint": endpoint,
                "error": str(e),
                "processing_time_ms": processing_time
            })
            raise NetworkError(f"Network error: {str(e)}", url=url)
        except json.JSONDecodeError as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error("JSON decode error in API request", extra={
                "component": "api_client",
                "operation": "make_request",
                "endpoint": endpoint,
                "error": str(e),
                "processing_time_ms": processing_time
            })
            raise ValidationError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error("Unexpected error in API request", extra={
                "component": "api_client",
                "operation": "make_request",
                "endpoint": endpoint,
                "error": str(e),
                "processing_time_ms": processing_time
            })
            raise NetworkError(f"Unexpected error: {str(e)}", url=url)
    
    async def make_streaming_request(self, endpoint: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Make streaming API request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Yields:
            Streaming response chunks
        """
        start_time = asyncio.get_event_loop().time()
        
        logger.info("Making streaming API request", extra={
            "component": "api_client",
            "operation": "make_streaming_request",
            "endpoint": endpoint,
            "data_size": len(str(data))
        })
        
        try:
            # Sanitize and validate data
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = self.sanitizer.sanitize_string(value)
                else:
                    sanitized_data[key] = value
            
            session = await self._get_session()
            url = f"{self.base_url}{endpoint}"
            
            async with session.post(url, json=sanitized_data) as response:
                processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                if response.status == 200:
                    chunk_count = 0
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data_str = line[6:]  # Remove 'data: ' prefix
                                if data_str:
                                    chunk_data = json.loads(data_str)
                                    chunk_count += 1
                                    yield chunk_data
                            except json.JSONDecodeError:
                                continue
                    
                    logger.info("Streaming API request completed", extra={
                        "component": "api_client",
                        "operation": "make_streaming_request",
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "chunk_count": chunk_count,
                        "processing_time_ms": processing_time
                    })
                else:
                    error_text = await response.text()
                    logger.error("Streaming API request failed", extra={
                        "component": "api_client",
                        "operation": "make_streaming_request",
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "error_text": error_text,
                        "processing_time_ms": processing_time
                    })
                    yield {"type": "error", "message": f"API request failed: {error_text}"}
                    
        except aiohttp.ClientError as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error("Network error in streaming request", extra={
                "component": "api_client",
                "operation": "make_streaming_request",
                "endpoint": endpoint,
                "error": str(e),
                "processing_time_ms": processing_time
            })
            yield {"type": "error", "message": f"Network error: {str(e)}"}
        except Exception as e:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error("Unexpected error in streaming request", extra={
                "component": "api_client",
                "operation": "make_streaming_request",
                "endpoint": endpoint,
                "error": str(e),
                "processing_time_ms": processing_time
            })
            yield {"type": "error", "message": f"Unexpected error: {str(e)}"}
    
    async def close(self):
        """Close HTTP session properly."""
        async with self._session_lock:
            if self.session and not self.session.closed:
                logger.info("Closing aiohttp session", extra={
                    "component": "api_client",
                    "operation": "close_session"
                })
                await self.session.close()
                self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper cleanup."""
        await self.close()


class ChatAPIClient:
    """Specialized client for chat operations with proper resource management."""
    
    def __init__(self, api_client: APIClientInterface):
        self.api_client = api_client
        
        logger.info("ChatAPIClient initialized", extra={
            "component": "chat_api_client",
            "operation": "init"
        })
    
    async def send_chat_message(self, query: str, session_id: Optional[str] = None, 
                               top_k: int = 5, retrieval_method: str = "title_first") -> Dict[str, Any]:
        """
        Send chat message to API.
        
        Args:
            query: User query
            session_id: Session identifier
            top_k: Number of results to retrieve
            retrieval_method: Retrieval method
            
        Returns:
            Chat response
        """
        logger.info("Sending chat message", extra={
            "component": "chat_api_client",
            "operation": "send_chat_message",
            "session_id": session_id,
            "query_length": len(query),
            "top_k": top_k,
            "retrieval_method": retrieval_method
        })
        
        data = {
            "query": query,
            "session_id": session_id,
            "top_k": top_k,
            "retrieval_method": retrieval_method,
            "use_advanced_features": False
        }
        
        return await self.api_client.make_request("/chat", data)
    
    async def send_chat_message_stream(self, query: str, session_id: Optional[str] = None,
                                     top_k: int = 5, retrieval_method: str = "title_first"):
        """
        Send streaming chat message to API.
        
        Args:
            query: User query
            session_id: Session identifier
            top_k: Number of results to retrieve
            retrieval_method: Retrieval method
            
        Yields:
            Streaming response chunks
        """
        logger.info("Sending streaming chat message", extra={
            "component": "chat_api_client",
            "operation": "send_chat_message_stream",
            "session_id": session_id,
            "query_length": len(query),
            "top_k": top_k,
            "retrieval_method": retrieval_method
        })
        
        data = {
            "query": query,
            "session_id": session_id,
            "top_k": top_k,
            "retrieval_method": retrieval_method,
            "use_advanced_features": False
        }
        
        async for chunk in self.api_client.make_streaming_request("/stream", data):
            yield chunk
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get API health status.
        
        Returns:
            Health status information
        """
        logger.info("Getting health status", extra={
            "component": "chat_api_client",
            "operation": "get_health_status"
        })
        
        return await self.api_client.make_request("/health", {})
    
    async def close(self):
        """Close underlying API client."""
        if hasattr(self.api_client, 'close'):
            await self.api_client.close()


@asynccontextmanager
async def create_api_client_context(base_url: str = "http://localhost:3001"):
    """
    Context manager for creating and properly closing API clients.
    
    Args:
        base_url: API base URL
        
    Yields:
        ChatAPIClient instance
    """
    api_client = APIClient(base_url)
    chat_client = ChatAPIClient(api_client)
    
    try:
        yield chat_client
    finally:
        await chat_client.close()


def create_api_client(base_url: str = "http://localhost:3001") -> ChatAPIClient:
    """
    Create API client instance.
    
    Args:
        base_url: API base URL
        
    Returns:
        ChatAPIClient instance
    """
    api_client = APIClient(base_url)
    return ChatAPIClient(api_client) 