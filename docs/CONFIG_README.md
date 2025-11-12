# Centralized Configuration System

This project now uses a centralized configuration system that consolidates all environment variables into a single `app/config.py` file. This ensures consistent configuration management across both server and frontend components.

## Overview

The centralized config system provides:
- **Single source of truth** for all environment variables
- **Type-safe configuration** with proper defaults
- **Validation** of required environment variables
- **Backward compatibility** with existing code
- **Support for both server and frontend usage patterns**

## Usage Patterns

### Server Usage (`python -m app.api`)

When running the server from the project root:

```python
from app.config import Config

# Access configuration values
api_url = Config.API_URL
groq_key = Config.GROQ_API_KEY
model = Config.GROQ_MODEL

# Validate required configs
Config.validate_required_configs()
```

### Frontend Usage (`streamlit run app/app.py`)

When running the frontend from the app directory:

```python
from config import Config

# Access configuration values
api_url = Config.API_URL
api_host = Config.API_HOST
api_port = Config.API_PORT
```

### Legacy Compatibility

For backward compatibility, you can still use the legacy function:

```python
from app.config import get_config

api_url = get_config("API_URL", "http://localhost:3001")
groq_key = get_config("GROQ_API_KEY")
```

## Configuration Variables

### API Configuration
- `API_URL`: The URL for the API server (default: "http://localhost:3001")
- `API_HOST`: Host for the API server (default: "0.0.0.0")
- `API_PORT`: Port for the API server (default: 3001)

### Groq Configuration
- `GROQ_API_KEY`: Your Groq API key (required)
- `GROQ_MODEL`: Groq model to use (default: "llama-3.3-70b-versatile")

### RAG Configuration
- `MAX_CONTEXT_LENGTH`: Maximum context length for LLM (default: 3000)
- `TOP_K_RETRIEVAL`: Number of documents to retrieve (default: 5)

### Memory Configuration
- `MEMORY_MAX_ENTRIES`: Maximum conversation entries to store (default: 10)
- `MEMORY_MAX_AGE_HOURS`: Maximum age of conversation entries (default: 24)
- `MEMORY_ENABLED`: Enable/disable conversation memory (default: true)

### Supabase Configuration
- `SUPABASE_URL`: Your Supabase project URL (required)
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key (required)

### Qdrant Configuration
- `QDRANT_URL`: Qdrant vector database URL (default: "http://localhost:6333")
- `QDRANT_API_KEY`: Qdrant API key (optional)

### Embedding Configuration
- `EMBEDDING_MODEL`: Embedding model to use (default: "sentence-transformers/all-MiniLM-L6-v2")
- `EMBEDDING_VECTOR_SIZE`: Vector size for embeddings (default: 384)
- `EMBEDDING_BATCH_SIZE`: Batch size for embedding processing (default: 100)
- `EMBEDDING_COLLECTION_PREFIX`: Prefix for Qdrant collections (default: "amazon_products")

### Logging Configuration
- `LOG_LEVEL`: Logging level (default: "INFO")

## Environment File Setup

Create a `.env` file in the project root with your configuration:

```env
# API Configuration
API_URL=http://localhost:3001
API_HOST=0.0.0.0
API_PORT=3001

# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# RAG Configuration
MAX_CONTEXT_LENGTH=3000
TOP_K_RETRIEVAL=5

# Memory Configuration
MEMORY_MAX_ENTRIES=10
MEMORY_MAX_AGE_HOURS=24
MEMORY_ENABLED=true

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_VECTOR_SIZE=384
EMBEDDING_BATCH_SIZE=100
EMBEDDING_COLLECTION_PREFIX=amazon_products

# Logging Configuration
LOG_LEVEL=INFO
```

## Validation

The config system includes validation for required environment variables:

```python
from app.config import Config

try:
    Config.validate_required_configs()
    print("✅ All required configs are set")
except ValueError as e:
    print(f"❌ Missing required configs: {e}")
```

## Getting All Configs

You can get all configuration values as a dictionary:

```python
from app.config import Config

all_configs = Config.get_all_configs()
for key, value in all_configs.items():
    print(f"{key}: {value}")
```

## Migration Guide

### Before (Old Way)
```python
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
```

### After (New Way)
```python
from app.config import Config

GROQ_API_KEY = Config.GROQ_API_KEY
GROQ_MODEL = Config.GROQ_MODEL
```

## Testing

Run the test script to verify configuration imports work correctly:

```bash
python test_config_imports.py
```

Run the embeddings test script to verify embeddings configuration:

```bash
python test_embeddings_config.py
```

Run the examples to see different usage patterns:

```bash
python config_usage_examples.py
```

### Running Embeddings Files

The embeddings files can be run from different directories:

**From project root:**
```bash
cd rag-demo
python embeddings/create_multivector_docs.py
python embeddings/build_embeddings.py
```

**From embeddings directory:**
```bash
cd rag-demo/embeddings
python3 create_multivector_docs.py
python3 build_embeddings.py
```

**Test embeddings imports:**
```bash
cd rag-demo/embeddings
python3 test_embeddings_imports.py
```

## Benefits

1. **Centralized Management**: All environment variables are managed in one place
2. **Type Safety**: Configuration values have proper types and defaults
3. **Validation**: Required environment variables are validated at startup
4. **Flexibility**: Supports both server and frontend usage patterns
5. **Backward Compatibility**: Existing code continues to work
6. **Documentation**: All configuration options are clearly documented
7. **Testing**: Easy to test configuration loading and validation 