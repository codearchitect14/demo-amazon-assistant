"""
Advanced Performance Optimization for RAG Systems
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from functools import lru_cache
import redis
import pickle
import hashlib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""

    enable_caching: bool = True
    enable_batching: bool = True
    enable_parallel_processing: bool = True
    cache_ttl: int = 3600  # 1 hour
    batch_size: int = 10
    max_workers: int = 4
    enable_async_processing: bool = True
    enable_connection_pooling: bool = True
    enable_compression: bool = True


class PerformanceOptimizer:
    """Advanced performance optimization for RAG systems"""

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()

        # Initialize cache
        if self.config.enable_caching:
            self._init_cache()

        # Initialize thread pool for parallel processing
        if self.config.enable_parallel_processing:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        else:
            self.thread_pool = None

        # Performance monitoring
        self.performance_stats = defaultdict(list)
        self.cache_stats = {"hits": 0, "misses": 0}

        logger.info(f"Performance optimizer initialized with config: {self.config}")

    def _init_cache(self):
        """Initialize caching system"""
        try:
            # Try to connect to Redis for distributed caching
            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=0, decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
            self.redis_client = None
            self.memory_cache = {}

    def cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key for function call"""
        # Create a hash of the function name and arguments
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result"""
        if not self.config.enable_caching:
            return None

        try:
            if self.redis_client:
                # Try Redis first
                cached = self.redis_client.get(cache_key)
                if cached:
                    self.cache_stats["hits"] += 1
                    return pickle.loads(cached.encode())
            else:
                # Use in-memory cache
                if cache_key in self.memory_cache:
                    self.cache_stats["hits"] += 1
                    return self.memory_cache[cache_key]

            self.cache_stats["misses"] += 1
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set_cached_result(self, cache_key: str, result: Any):
        """Set cached result"""
        if not self.config.enable_caching:
            return

        try:
            if self.redis_client:
                # Store in Redis
                serialized = pickle.dumps(result)
                self.redis_client.setex(cache_key, self.config.cache_ttl, serialized)
            else:
                # Store in memory
                self.memory_cache[cache_key] = result
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def cached_function(self, func: Callable) -> Callable:
        """Decorator for caching function results"""

        def wrapper(*args, **kwargs):
            cache_key = self.cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            self.set_cached_result(cache_key, result)
            return result

        return wrapper

    async def cached_async_function(self, func: Callable) -> Callable:
        """Decorator for caching async function results"""

        async def wrapper(*args, **kwargs):
            cache_key = self.cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            self.set_cached_result(cache_key, result)
            return result

        return wrapper

    def batch_processor(self, batch_size: int = None):
        """Decorator for batch processing"""

        def decorator(func: Callable) -> Callable:
            batch_queue = []
            batch_size_actual = batch_size or self.config.batch_size

            def wrapper(*args, **kwargs):
                # Add to batch queue
                batch_queue.append((args, kwargs))

                # Process batch if full
                if len(batch_queue) >= batch_size_actual:
                    return self._process_batch(func, batch_queue)
                else:
                    # Return placeholder for single item
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def _process_batch(self, func: Callable, batch_items: List) -> List[Any]:
        """Process a batch of function calls"""
        try:
            results = []
            for args, kwargs in batch_items:
                result = func(*args, **kwargs)
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return []

    async def parallel_async_processing(
        self, tasks: List[Callable], *args, **kwargs
    ) -> List[Any]:
        """Process multiple async tasks in parallel"""
        try:

            async def execute_task(task):
                try:
                    return await task(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Task execution error: {e}")
                    return None

            # Execute tasks concurrently
            results = await asyncio.gather(*[execute_task(task) for task in tasks])
            return [r for r in results if r is not None]
        except Exception as e:
            logger.error(f"Parallel processing error: {e}")
            return []

    def connection_pool(self, pool_size: int = 10):
        """Decorator for connection pooling"""

        def decorator(func: Callable) -> Callable:
            # Create connection pool
            connections = []

            def wrapper(*args, **kwargs):
                # Get connection from pool
                if connections:
                    connection = connections.pop()
                else:
                    connection = self._create_connection()

                try:
                    # Execute function with connection
                    result = func(connection, *args, **kwargs)
                    return result
                finally:
                    # Return connection to pool
                    if len(connections) < pool_size:
                        connections.append(connection)
                    else:
                        self._close_connection(connection)

            return wrapper

        return decorator

    def _create_connection(self):
        """Create a new connection"""
        # This would be implemented based on the specific connection type
        return None

    def _close_connection(self, connection):
        """Close a connection"""
        # This would be implemented based on the specific connection type
        pass

    def performance_monitor(self, func: Callable) -> Callable:
        """Decorator for performance monitoring"""

        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = self._get_memory_usage()

            try:
                result = func(*args, **kwargs)

                # Record performance metrics
                execution_time = time.time() - start_time
                memory_used = self._get_memory_usage() - start_memory

                self.performance_stats[func.__name__].append(
                    {
                        "execution_time": execution_time,
                        "memory_used": memory_used,
                        "timestamp": time.time(),
                    }
                )

                return result
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                raise

        return wrapper

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0

    def optimize_embeddings_batch(
        self, texts: List[str], batch_size: int = None
    ) -> List[List[float]]:
        """Optimize embedding generation with batching"""
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")
            batch_size_actual = batch_size or self.config.batch_size

            embeddings = []
            for i in range(0, len(texts), batch_size_actual):
                batch = texts[i : i + batch_size_actual]
                batch_embeddings = model.encode(batch)
                embeddings.extend(batch_embeddings)

            return embeddings
        except Exception as e:
            logger.error(f"Embedding optimization error: {e}")
            return []

    def _embed_single(self, text: str) -> List[float]:
        """Embed a single text"""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode([text])[0].tolist()

    def optimize_vector_search(
        self, query_embedding: List[float], collection_name: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Optimize vector search performance"""
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient("localhost", port=6333)

            # Perform optimized search
            search_result = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

            return [
                {"id": result.id, "score": result.score, "payload": result.payload}
                for result in search_result
            ]
        except Exception as e:
            logger.error(f"Vector search optimization error: {e}")
            return []

    def _perform_vector_search(
        self, query_embedding: List[float], collection_name: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform basic vector search"""
        # This would be implemented based on your vector database
        return []

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {
            "cache_stats": dict(self.cache_stats),
            "performance_stats": {},
            "memory_usage": self._get_memory_usage(),
            "config": {
                "enable_caching": self.config.enable_caching,
                "enable_batching": self.config.enable_batching,
                "enable_parallel_processing": self.config.enable_parallel_processing,
                "cache_ttl": self.config.cache_ttl,
                "batch_size": self.config.batch_size,
                "max_workers": self.config.max_workers,
            },
        }

        # Calculate performance metrics for each function
        for func_name, metrics in self.performance_stats.items():
            if metrics:
                execution_times = [m["execution_time"] for m in metrics]
                memory_usage = [m["memory_used"] for m in metrics]

                stats["performance_stats"][func_name] = {
                    "avg_execution_time": sum(execution_times) / len(execution_times),
                    "max_execution_time": max(execution_times),
                    "min_execution_time": min(execution_times),
                    "avg_memory_usage": sum(memory_usage) / len(memory_usage),
                    "total_calls": len(metrics),
                }

        return stats

    def clear_cache(self):
        """Clear all caches"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()

            self.cache_stats = {"hits": 0, "misses": 0}
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def optimize_rag_pipeline(
        self, query: str, context: str, conversation_history: str = ""
    ) -> Dict[str, Any]:
        """Optimize RAG pipeline performance"""
        try:
            start_time = time.time()

            # Optimize context processing
            if len(context) > 10000:  # Large context
                # Truncate or summarize context
                context = context[:10000]

            # Optimize conversation history
            if len(conversation_history) > 5000:  # Large history
                # Truncate history
                conversation_history = conversation_history[-5000:]

            # Measure optimization time
            optimization_time = time.time() - start_time

            return {
                "optimized_context_length": len(context),
                "optimized_history_length": len(conversation_history),
                "optimization_time": optimization_time,
                "original_query": query,
            }
        except Exception as e:
            logger.error(f"RAG pipeline optimization error: {e}")
            return {"error": str(e), "optimization_time": 0.0}

    def _execute_optimized_pipeline(
        self, query: str, context: str, conversation_history: str
    ) -> Dict[str, Any]:
        """Execute optimized RAG pipeline"""
        try:
            # This would contain the actual RAG pipeline execution
            # with all optimizations applied
            return {
                "query": query,
                "context": context,
                "conversation_history": conversation_history,
                "optimized": True,
            }
        except Exception as e:
            logger.error(f"Optimized pipeline execution error: {e}")
            return {"error": str(e)}
