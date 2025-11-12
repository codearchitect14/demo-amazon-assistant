# Comprehensive Token Tracking

This feature provides detailed token tracking for every query in the RAG pipeline, displaying information in rich tabular format.

## Features

- **Real-time token counting** for all pipeline components
- **Rich tabular output** with detailed breakdowns
- **Session-based tracking** for conversation history
- **Token statistics** and analytics
- **File logging** for persistent tracking

## Components Tracked

1. **User Prompt** - The user's question
2. **System Prompt** - The system instructions
3. **Conversation History** - Previous interactions
4. **Retrieved Context** - Retrieved documents
5. **LLM Response** - Generated answer
6. **Total Input Tokens** - Sum of all input components

## Usage

### Basic Usage

```python
from rich_logging import log_comprehensive_token_breakdown

# Log token breakdown for a query
query_data = {
    "user_prompt": "What are the best features?",
    "system_prompt": "You are a helpful assistant...",
    "conversation_history": "Previous conversation...",
    "retrieved_context": "Retrieved information...",
    "llm_response": "Generated answer..."
}

log_comprehensive_token_breakdown("session_123", query_data)
```

### Integration with RAG Pipeline

The token tracking is automatically integrated into the RAG pipeline:

```python
from rag.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
result = await pipeline.run_rag_pipeline_async(
    question="Your question here",
    session_id="your_session_id"
)
# Token breakdown will be automatically logged
```

## Output Format

The system displays:

1. **Summary Panel** - Session info and total tokens
2. **Detailed Table** - Component-by-component breakdown
3. **Statistics** - Overall token usage

## Test Scripts

- `test_comprehensive_token_tracking.py` - Test the token tracking functionality
- `demo_token_tracking.py` - Demo with actual RAG pipeline

## Configuration

Token tracking is enabled by default. Configure in `rich_logging.py`:

```python
rich_logger = RichLogger(
    enable_rich=True,      # Enable rich output
    log_to_file=True,      # Save to file
    log_file="rag_pipeline.log"
)
```

## Token Counting

Uses `tiktoken` for accurate token counting with fallback to character-based estimation. 