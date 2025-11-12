# Embedding Model Cache Implementation

This document describes the embedding model caching functionality that has been implemented to improve performance and manage memory efficiently.

## Overview

The embedding model cache provides automatic lifecycle management for the sentence transformer model used in the RAG system:
- **Loads model into memory** on first use
- **2-hour lifetime** that resets on new queries
- **Automatic cleanup** when server shuts down
- **Thread-safe** operations with background monitoring

## Architecture

### EmbeddingModelCache Class

The core caching functionality is implemented in `rag/embedding_cache.py`:

```python
class EmbeddingModelCache:
    def __init__(self, model_name: str = None, lifetime_hours: int = 2):
        # Initialize with 2-hour default lifetime
        self.lifetime_seconds = lifetime_hours * 3600
        self.model = None
        self.last_used_time = None
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
```

### Key Features

1. **Lazy Loading**: Model is loaded only when first needed
2. **Lifetime Management**: 2-hour lifetime that resets on each access
3. **Background Cleanup**: Daemon thread monitors and cleans up expired models
4. **Thread Safety**: All operations are protected with locks
5. **Graceful Shutdown**: Proper cleanup on server shutdown

## API Endpoints

### Get Cache Status
```
GET /embedding/cache/status
```

**Response:**
```json
{
  "embedding_cache": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "model_loaded": true,
    "last_used_time": 1640995200.0,
    "time_since_last_use_seconds": 300.5,
    "time_until_expiry_seconds": 6900.5,
    "lifetime_seconds": 7200,
    "shutdown_requested": false
  },
  "message": "Embedding cache status retrieved successfully"
}
```

### Force Reload Model
```
POST /embedding/cache/reload
```

**Response:**
```json
{
  "message": "Embedding model reload initiated",
  "status": "success"
}
```

### Clear Model from Memory
```
POST /embedding/cache/clear
```

**Response:**
```json
{
  "message": "Embedding model cleared from memory",
  "status": "success"
}
```

## Integration with Retriever

The retriever has been updated to use the cached embeddings:

```python
class CachedHuggingFaceEmbeddings(HuggingFaceEmbeddings):
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name=model_name, **kwargs)
        self.cache = get_embedding_cache()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.cache.encode(texts).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        return self.cache.encode_single(text).tolist()
```

## Lifecycle Management

### 1. **Initialization**
- Cache is created when first accessed
- Model is not loaded until first use
- Background cleanup thread starts

### 2. **Model Loading**
- Triggered by first embedding request
- Model loaded into memory
- Lifetime timer starts

### 3. **Lifetime Reset**
- Each new query resets the 2-hour timer
- Model stays in memory as long as it's being used

### 4. **Automatic Cleanup**
- Background thread checks every 5 minutes
- Expired models (unused for 2+ hours) are cleared
- Memory is freed automatically

### 5. **Server Shutdown**
- Signal handlers (SIGINT, SIGTERM) trigger cleanup
- FastAPI shutdown event also triggers cleanup
- Model is properly unloaded from memory

## Performance Benefits

### ✅ **Improved Response Time**
- No model loading delay on subsequent queries
- Faster embedding generation

### ✅ **Memory Efficiency**
- Automatic cleanup of unused models
- Prevents memory leaks

### ✅ **Resource Management**
- 2-hour lifetime prevents long-term memory usage
- Graceful shutdown ensures clean state

### ✅ **Thread Safety**
- Safe concurrent access
- No race conditions

## Usage Examples

### Check Cache Status
```bash
curl http://localhost:3001/embedding/cache/status
```

### Force Reload
```bash
curl -X POST http://localhost:3001/embedding/cache/reload
```

### Clear Cache
```bash
curl -X POST http://localhost:3001/embedding/cache/clear
```

## Testing

Run the embedding cache test:
```bash
cd rag-demo
python test_embedding_cache.py
```

This will test:
- Cache status retrieval
- Model reloading
- Cache clearing
- Complete lifecycle management

## Monitoring

### Log Messages
The cache provides detailed logging:
- Model loading/unloading
- Lifetime resets
- Cleanup operations
- Error conditions

### Metrics Available
- Model load status
- Time since last use
- Time until expiry
- Memory usage (indirect)

## Configuration

### Environment Variables
- `EMBEDDING_MODEL`: Model name (default: "sentence-transformers/all-MiniLM-L6-v2")
- Cache lifetime is configurable in the EmbeddingModelCache constructor

### Customization
```python
# Custom lifetime (4 hours)
cache = EmbeddingModelCache(lifetime_hours=4)

# Custom model
cache = EmbeddingModelCache(model_name="custom-model")
```

## Troubleshooting

### Common Issues

1. **Model not loading**: Check if the model name is correct and accessible
2. **Memory issues**: Monitor cache status and clear if needed
3. **Performance problems**: Check if model is loaded and being reused

### Debug Information
Use the `/embedding/cache/status` endpoint to get detailed information about the cache state.

## Future Enhancements

- [ ] Add memory usage monitoring
- [ ] Implement cache warming strategies
- [ ] Add multiple model support
- [ ] Implement cache persistence
- [ ] Add cache performance metrics 