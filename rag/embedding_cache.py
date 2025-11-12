import time
import logging
import threading
from typing import Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import Config

logger = logging.getLogger(__name__)


class EmbeddingModelCache:
    """
    Embedding model cache with automatic lifecycle management.
    - Loads model into memory on first use
    - 2-hour lifetime that resets on new queries
    - Clears when server shuts down
    """

    def __init__(self, model_name: str = None, lifetime_hours: int = 2):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.lifetime_seconds = lifetime_hours * 3600
        self.model: Optional[SentenceTransformer] = None
        self.last_used_time: Optional[float] = None
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()

        logger.info(
            f"EmbeddingModelCache initialized with model: {self.model_name}, lifetime: {lifetime_hours}h"
        )

    def get_model(self) -> SentenceTransformer:
        """
        Get the embedding model, loading it if necessary.
        Resets the lifetime timer on each access.
        """
        with self._lock:
            current_time = time.time()

            # Check if model needs to be loaded or reloaded
            if (
                self.model is None
                or self.last_used_time is None
                or current_time - self.last_used_time > self.lifetime_seconds
            ):

                # Clear old model if it exists
                if self.model is not None:
                    logger.info("Clearing old embedding model from memory")
                    del self.model
                    self.model = None

                # Load new model
                logger.info(f"Loading embedding model: {self.model_name}")
                try:
                    self.model = SentenceTransformer(self.model_name)
                    logger.info(
                        f"Successfully loaded embedding model: {self.model_name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load embedding model {self.model_name}: {e}"
                    )
                    raise

            # Update last used time
            self.last_used_time = current_time
            logger.debug(
                f"Embedding model accessed, lifetime reset. Model loaded: {self.model is not None}"
            )

            return self.model

    def encode(self, texts: list, **kwargs) -> list:
        """
        Encode texts using the cached model.
        """
        logger.info(f"Encoding {len(texts)} texts using cached model")
        model = self.get_model()
        result = model.encode(texts, **kwargs)
        logger.info(f"Successfully encoded {len(texts)} texts")
        return result.tolist()

    def encode_single(self, text: str, **kwargs) -> list:
        """
        Encode a single text using the cached model.
        """
        logger.info(f"Encoding single text using cached model")
        model = self.get_model()
        result = model.encode([text], **kwargs)[0]
        logger.info(f"Successfully encoded single text")
        return result.tolist()

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model state.
        """
        with self._lock:
            current_time = time.time()
            time_since_last_use = (
                current_time - self.last_used_time if self.last_used_time else None
            )
            time_until_expiry = (
                self.lifetime_seconds - time_since_last_use
                if time_since_last_use
                else None
            )

            return {
                "model_name": self.model_name,
                "model_loaded": self.model is not None,
                "last_used_time": self.last_used_time,
                "time_since_last_use_seconds": time_since_last_use,
                "time_until_expiry_seconds": time_until_expiry,
                "lifetime_seconds": self.lifetime_seconds,
                "shutdown_requested": self._shutdown_event.is_set(),
            }

    def force_reload(self):
        """
        Force reload the model regardless of lifetime.
        """
        with self._lock:
            logger.info("Force reloading embedding model")
            if self.model is not None:
                del self.model
                self.model = None
            self.last_used_time = None
            # Model will be loaded on next get_model() call

    def clear_cache(self):
        """
        Clear the model from memory.
        """
        with self._lock:
            logger.info("Clearing embedding model cache")
            if self.model is not None:
                del self.model
                self.model = None
            self.last_used_time = None

    def _cleanup_worker(self):
        """
        Background thread that monitors model lifetime and cleans up expired models.
        """
        while not self._shutdown_event.is_set():
            try:
                # Sleep for 5 minutes before checking
                if self._shutdown_event.wait(300):  # 5 minutes
                    break

                with self._lock:
                    if (
                        self.model is not None
                        and self.last_used_time is not None
                        and time.time() - self.last_used_time > self.lifetime_seconds
                    ):

                        logger.info("Embedding model expired, clearing from memory")
                        del self.model
                        self.model = None
                        self.last_used_time = None

            except Exception as e:
                logger.error(f"Error in embedding cache cleanup worker: {e}")

    def shutdown(self):
        """
        Shutdown the cache and cleanup resources.
        """
        logger.info("Shutting down embedding model cache")
        self._shutdown_event.set()

        # Wait for cleanup thread to finish
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

        # Clear model
        self.clear_cache()
        logger.info("Embedding model cache shutdown complete")


# Global instance
_embedding_cache: Optional[EmbeddingModelCache] = None


def get_embedding_cache() -> EmbeddingModelCache:
    """
    Get the global embedding cache instance.
    """
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingModelCache()
    return _embedding_cache


def shutdown_embedding_cache():
    """
    Shutdown the global embedding cache.
    """
    global _embedding_cache
    if _embedding_cache is not None:
        _embedding_cache.shutdown()
        _embedding_cache = None
