import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration class for all environment variables"""

    # API Configuration
    API_URL = os.getenv("API_URL", "http://localhost:3001")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "3001"))

    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_PRIMARY_MODEL = os.getenv("GROQ_PRIMARY_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")
    GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")

    # Resilience Configuration
    ENABLE_CIRCUIT_BREAKER = (
        os.getenv("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true"
    )
    ENABLE_RETRY_LOGIC = os.getenv("ENABLE_RETRY_LOGIC", "true").lower() == "true"
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(
        os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")
    )
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(
        os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60")
    )
    RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
    RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "60.0"))

    # RAG Configuration
    MAX_CONTEXT_LENGTH = None
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    DEFAULT_RETRIEVAL_METHOD = os.getenv("DEFAULT_RETRIEVAL_METHOD", "title_first")

    # Available retrieval methods
    RETRIEVAL_METHODS = [
        "multi",
        "weighted",
        "title",
        "reviews",
        "qa",
        "title_first",
        "hybrid",
        "hierarchical",
    ]

    # Memory Configuration
    MEMORY_MAX_ENTRIES = int(os.getenv("MEMORY_MAX_ENTRIES", "10"))
    MEMORY_MAX_AGE_HOURS = int(os.getenv("MEMORY_MAX_AGE_HOURS", "24"))
    MEMORY_ENABLED = os.getenv("MEMORY_ENABLED", "true").lower() == "true"

    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_TTL_HOURS = int(os.getenv("REDIS_TTL_HOURS", "24"))
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_MAX_ENTRIES = int(os.getenv("REDIS_MAX_ENTRIES", "50"))
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

    # Qdrant Configuration
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    # Embedding Configuration
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_VECTOR_SIZE = int(os.getenv("EMBEDDING_VECTOR_SIZE", "384"))
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    EMBEDDING_COLLECTION_PREFIX = os.getenv(
        "EMBEDDING_COLLECTION_PREFIX", "amazon_products"
    )

    # Advanced Features Configuration
    ENABLE_HYBRID_SEARCH = os.getenv("ENABLE_HYBRID_SEARCH", "false").lower() == "true"
    ENABLE_CROSS_ENCODER = os.getenv("ENABLE_CROSS_ENCODER", "false").lower() == "true"
    ENABLE_QUERY_EXPANSION = (
        os.getenv("ENABLE_QUERY_EXPANSION", "false").lower() == "true"
    )
    ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "false").lower() == "true"
    ENABLE_EVALUATION = os.getenv("ENABLE_EVALUATION", "false").lower() == "true"
    ENABLE_PERFORMANCE_OPTIMIZATION = (
        os.getenv("ENABLE_PERFORMANCE_OPTIMIZATION", "false").lower() == "true"
    )
    ENABLE_STRUCTURED_PROMPTS = (
        os.getenv("ENABLE_STRUCTURED_PROMPTS", "false").lower() == "true"
    )

    # Cross-Encoder Configuration
    CROSS_ENCODER_MODEL = os.getenv(
        "CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )

    # Performance Configuration
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

    # Evaluation Configuration
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.7"))
    ACCURACY_THRESHOLD = float(os.getenv("ACCURACY_THRESHOLD", "0.8"))
    HALLUCINATION_THRESHOLD = float(os.getenv("HALLUCINATION_THRESHOLD", "0.3"))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate_required_configs(cls) -> None:
        """Validate that all required environment variables are set"""
        required_configs = {
            "GROQ_API_KEY": cls.GROQ_API_KEY,
        }

        missing_configs = [key for key, value in required_configs.items() if not value]

        if missing_configs:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_configs)}"
            )

    @classmethod
    def get_all_configs(cls) -> Dict[str, Any]:
        """Get all configuration values as a dictionary"""
        return {
            "API_URL": cls.API_URL,
            "API_HOST": cls.API_HOST,
            "API_PORT": cls.API_PORT,
            "GROQ_API_KEY": cls.GROQ_API_KEY,
            "GROQ_PRIMARY_MODEL": cls.GROQ_PRIMARY_MODEL,
            "GROQ_FALLBACK_API_KEY": cls.GROQ_FALLBACK_API_KEY,
            "GROQ_FALLBACK_MODEL": cls.GROQ_FALLBACK_MODEL,
            "ENABLE_CIRCUIT_BREAKER": cls.ENABLE_CIRCUIT_BREAKER,
            "ENABLE_RETRY_LOGIC": cls.ENABLE_RETRY_LOGIC,
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": cls.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": cls.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            "RETRY_MAX_ATTEMPTS": cls.RETRY_MAX_ATTEMPTS,
            "RETRY_BASE_DELAY": cls.RETRY_BASE_DELAY,
            "RETRY_MAX_DELAY": cls.RETRY_MAX_DELAY,
            "MAX_CONTEXT_LENGTH": cls.MAX_CONTEXT_LENGTH,
            "TOP_K_RETRIEVAL": cls.TOP_K_RETRIEVAL,
            "DEFAULT_RETRIEVAL_METHOD": cls.DEFAULT_RETRIEVAL_METHOD,
            "RETRIEVAL_METHODS": cls.RETRIEVAL_METHODS,
            "MEMORY_MAX_ENTRIES": cls.MEMORY_MAX_ENTRIES,
            "MEMORY_MAX_AGE_HOURS": cls.MEMORY_MAX_AGE_HOURS,
            "MEMORY_ENABLED": cls.MEMORY_ENABLED,
            "REDIS_URL": cls.REDIS_URL,
            "REDIS_TTL_HOURS": cls.REDIS_TTL_HOURS,
            "REDIS_ENABLED": cls.REDIS_ENABLED,
            "REDIS_MAX_ENTRIES": cls.REDIS_MAX_ENTRIES,
            "REDIS_HOST": cls.REDIS_HOST,
            "REDIS_PORT": cls.REDIS_PORT,
            "REDIS_DB": cls.REDIS_DB,
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_ANON_KEY": cls.SUPABASE_ANON_KEY,
            "QDRANT_URL": cls.QDRANT_URL,
            "QDRANT_API_KEY": cls.QDRANT_API_KEY,
            "EMBEDDING_MODEL": cls.EMBEDDING_MODEL,
            "EMBEDDING_VECTOR_SIZE": cls.EMBEDDING_VECTOR_SIZE,
            "EMBEDDING_BATCH_SIZE": cls.EMBEDDING_BATCH_SIZE,
            "EMBEDDING_COLLECTION_PREFIX": cls.EMBEDDING_COLLECTION_PREFIX,
            "ENABLE_HYBRID_SEARCH": cls.ENABLE_HYBRID_SEARCH,
            "ENABLE_CROSS_ENCODER": cls.ENABLE_CROSS_ENCODER,
            "ENABLE_QUERY_EXPANSION": cls.ENABLE_QUERY_EXPANSION,
            "ENABLE_RERANKING": cls.ENABLE_RERANKING,
            "ENABLE_EVALUATION": cls.ENABLE_EVALUATION,
            "ENABLE_PERFORMANCE_OPTIMIZATION": cls.ENABLE_PERFORMANCE_OPTIMIZATION,
            "ENABLE_STRUCTURED_PROMPTS": cls.ENABLE_STRUCTURED_PROMPTS,
            "CROSS_ENCODER_MODEL": cls.CROSS_ENCODER_MODEL,
            "CACHE_TTL": cls.CACHE_TTL,
            "BATCH_SIZE": cls.BATCH_SIZE,
            "MAX_WORKERS": cls.MAX_WORKERS,
            "RELEVANCE_THRESHOLD": cls.RELEVANCE_THRESHOLD,
            "ACCURACY_THRESHOLD": cls.ACCURACY_THRESHOLD,
            "HALLUCINATION_THRESHOLD": cls.HALLUCINATION_THRESHOLD,
            "LOG_LEVEL": cls.LOG_LEVEL,
        }


# Legacy function for backward compatibility
def get_config(key: str, default=None):
    """Legacy function for backward compatibility"""
    return (
        getattr(Config, key, default)
        if hasattr(Config, key)
        else os.getenv(key, default)
    )


# Create a config instance for easy access
config = Config()
