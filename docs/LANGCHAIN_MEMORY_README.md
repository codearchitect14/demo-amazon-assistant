# LangChain Conversation Memory Implementation

This document describes the implementation of LangChain's `ConversationBufferMemory` with session ID support for the RAG pipeline.

## Overview

The LangChain conversation memory implementation provides:
- **Session-based memory**: Each conversation session has its own isolated memory buffer
- **LangChain integration**: Uses LangChain's `ConversationBufferMemory` for robust conversation handling
- **Async support**: Full async/await support for all operations
- **Automatic cleanup**: Sessions are automatically cleaned up based on age
- **Memory statistics**: Comprehensive memory usage tracking

## Features

### 1. Session ID Support
- Each conversation session has a unique session ID
- Memory is isolated per session
- Multiple sessions can run concurrently

### 2. LangChain Integration
- Uses `ConversationBufferMemory` from LangChain
- Proper message handling with `HumanMessage` and `AIMessage`
- Compatible with LangChain's memory patterns

### 3. Memory Management
- Automatic cleanup of old sessions
- Configurable max entries and age limits
- Memory statistics and health monitoring

## Usage

### Basic Usage

```python
from rag.rag_utils import LangChainConversationMemory

# Create memory instance
memory = LangChainConversationMemory()

# Add interaction
session_id = "user_123"
memory.add_interaction(session_id, "What are good headphones?", "Here are some good headphones...")

# Get recent context
context = memory.get_recent_context(session_id, max_entries=3)

# Get conversation summary
summary = memory.get_conversation_summary(session_id)
```

### Async Usage

```python
import asyncio

async def async_example():
    memory = LangChainConversationMemory()
    session_id = "user_456"
    
    # Add interaction async
    await memory.add_interaction_async(session_id, "Question", "Answer")
    
    # Get context async
    context = await memory.get_recent_context_async(session_id)
    
    # Get summary async
    summary = await memory.get_conversation_summary_async(session_id)
```

### RAG Pipeline Integration

```python
from rag.rag_pipeline import RAGPipeline

# Create RAG pipeline with LangChain memory
pipeline = RAGPipeline(enable_memory=True, memory_type="langchain")

# Run pipeline with session ID
result = pipeline.run_rag_pipeline(
    question="What are good wireless headphones?",
    session_id="user_789"
)

# Follow-up question (will use conversation history)
result2 = pipeline.run_rag_pipeline(
    question="Which of those have the best battery life?",
    session_id="user_789"  # Same session ID
)
```

## Memory Types

The RAG pipeline supports multiple memory types:

1. **`"langchain"`**: LangChain conversation buffer (recommended)
2. **`"redis"`**: Redis-based memory (requires Redis)
3. **`"in_memory"`**: Simple in-memory storage
4. **`"auto"`**: Automatic selection (Redis if available, otherwise LangChain)

```python
# Explicit LangChain memory
pipeline = RAGPipeline(memory_type="langchain")

# Auto-selection
pipeline = RAGPipeline(memory_type="auto")
```

## Configuration

### Environment Variables

```bash
# Memory settings
MEMORY_ENABLED=true
MEMORY_MAX_ENTRIES=10
MEMORY_MAX_AGE_HOURS=24

# Redis settings (optional)
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379
REDIS_TTL_HOURS=24
REDIS_MAX_ENTRIES=50
```

### Memory Parameters

```python
memory = LangChainConversationMemory(
    max_entries=10,      # Maximum interactions per session
    max_age_hours=24     # Session cleanup after 24 hours
)
```

## API Methods

### Core Methods

- `add_interaction(session_id, question, answer, context="", metadata=None)`
- `get_recent_context(session_id, max_entries=3)`
- `get_conversation_summary(session_id)`
- `clear_session(session_id)`
- `get_memory_stats()`

### Async Methods

- `add_interaction_async(session_id, question, answer, context="", metadata=None)`
- `get_recent_context_async(session_id, max_entries=3)`
- `get_conversation_summary_async(session_id)`
- `clear_session_async(session_id)`
- `get_memory_stats_async()`

## Memory Statistics

```python
stats = memory.get_memory_stats()
# Returns:
{
    'enabled': True,
    'type': 'langchain_conversation_buffer',
    'total_sessions': 5,
    'total_interactions': 15,
    'max_entries': 10,
    'max_age_hours': 24.0,
    'available': True
}
```

## Testing

Run the test script to verify functionality:

```bash
python test_langchain_memory.py
```

This will test:
- Synchronous memory operations
- Asynchronous memory operations
- RAG pipeline integration
- Multiple session handling
- Memory statistics

## Advantages of LangChain Memory

1. **Robust Message Handling**: Proper handling of `HumanMessage` and `AIMessage`
2. **LangChain Ecosystem**: Compatible with other LangChain components
3. **Memory Patterns**: Follows established conversation memory patterns
4. **Extensibility**: Easy to extend with other LangChain memory types
5. **Session Isolation**: Clean separation between different conversation sessions

## Comparison with Other Memory Types

| Feature | LangChain | Redis | In-Memory |
|---------|-----------|-------|-----------|
| Persistence | No | Yes | No |
| Session Isolation | Yes | Yes | Yes |
| LangChain Integration | Full | Partial | None |
| Performance | High | High | Very High |
| Scalability | Medium | High | Low |
| Setup Complexity | Low | Medium | Low |

## Best Practices

1. **Use session IDs**: Always provide unique session IDs for different conversations
2. **Clean up sessions**: Clear sessions when no longer needed
3. **Monitor memory usage**: Check memory statistics regularly
4. **Handle errors**: Wrap memory operations in try-catch blocks
5. **Use async when possible**: Prefer async methods for better performance

## Troubleshooting

### Common Issues

1. **Memory not working**: Check if `MEMORY_ENABLED=true` in config
2. **Sessions not persisting**: LangChain memory is in-memory only, use Redis for persistence
3. **Performance issues**: Consider using async methods or reducing max_entries
4. **Memory leaks**: Sessions are auto-cleaned, but you can manually clear old sessions

### Debug Information

```python
# Get detailed memory stats
stats = memory.get_memory_stats()
print(f"Memory type: {stats['type']}")
print(f"Active sessions: {stats['total_sessions']}")
print(f"Total interactions: {stats['total_interactions']}")
```

## Future Enhancements

1. **Persistent Storage**: Add database backend for session persistence
2. **Memory Types**: Support for `ConversationSummaryMemory`, `ConversationTokenBufferMemory`
3. **Vector Memory**: Integration with vector-based memory for semantic search
4. **Memory Chains**: Support for complex memory chains and workflows
5. **Memory Observability**: Enhanced monitoring and analytics 