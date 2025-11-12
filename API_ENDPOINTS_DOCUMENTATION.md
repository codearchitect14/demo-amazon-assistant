# RAG Demo API Endpoints Documentation

## Overview
This document describes all API endpoints in the RAG Demo application, their functionality, and how data is extracted and formatted.

## Base URL
- **Development**: `http://localhost:3001`
- **Production**: Configured via environment variables

---

## Chat Endpoints

### 1. POST `/chat`
**Purpose**: Process chat requests with RAG (Retrieval-Augmented Generation)

**Request Format**:
```json
{
  "query": "string (1-1000 chars)",
  "session_id": "string (optional, max 50 chars)",
  "top_k": "integer (1-100, default: 5)",
  "retrieval_method": "string (title_first|multi|hybrid|semantic, default: title_first)",
  "use_advanced_features": "boolean (default: false)"
}
```

**Response Format**:
```json
{
  "question": "string",
  "answer": "string",
  "context": "string",
  "intent": "object",
  "metadata": "object"
}
```

**Data Extraction & Processing**:
- Validates and sanitizes user query (removes malicious content, limits length)
- Retrieves relevant context using specified retrieval method
- Generates AI response using retrieved context
- Extracts intent information from user query
- Returns structured response with metadata

**Context Extraction Process**:
1. **Stream Processing**: Receives streaming chunks from API
2. **Context Parsing**: Extracts context from "complete" chunk type
3. **Product Extraction**: Uses `extract_products_from_context()` function
4. **Data Cleaning**: Applies `clean_product_title()` and `clean_product_price()`
5. **Session Storage**: Stores extracted products in session state

---

### 2. POST `/stream`
**Purpose**: Process streaming chat requests with real-time response generation

**Request Format**: Same as `/chat` endpoint

**Response Format**: Server-Sent Events (SSE) stream
```json
// Token chunks
{"type": "token", "content": "string"}

// Context information
{"type": "context", "content": "string", "intent": "object"}

// Completion signal
{"type": "complete", "context": "string", "metadata": "object"}

// Error responses
{"type": "error", "message": "string"}
```

**Data Extraction & Processing**:
- Streams response tokens in real-time
- Sends context information when available
- Provides completion metadata
- Handles errors gracefully with error events

**Context Processing in Frontend**:
1. **Chunk Processing**: Processes each streaming chunk
2. **Token Accumulation**: Builds full response from token chunks
3. **Context Extraction**: Extracts context from "complete" chunk
4. **Product Parsing**: Parses context for product information
5. **UI Updates**: Updates product gallery in sidebar

---

## Memory Endpoints

### 3. GET `/memory/stats`
**Purpose**: Get memory statistics and usage information

**Response Format**:
```json
{
  "total_sessions": "integer",
  "active_sessions": "integer",
  "memory_usage": "object",
  "performance_metrics": "object"
}
```

**Data Extraction**:
- Counts total and active sessions
- Calculates memory usage statistics
- Tracks performance metrics

---

### 4. DELETE `/memory/session/{session_id}`
**Purpose**: Clear memory for a specific session

**Parameters**:
- `session_id`: Session identifier

**Response Format**:
```json
{
  "status": "string",
  "session_id": "string",
  "cleared_messages": "integer"
}
```

**Data Processing**:
- Removes all conversation history for specified session
- Returns count of cleared messages

---

### 5. GET `/memory/session/{session_id}/history`
**Purpose**: Get conversation history for a session

**Parameters**:
- `session_id`: Session identifier

**Response Format**:
```json
{
  "session_id": "string",
  "messages": [
    {
      "role": "string",
      "content": "string",
      "timestamp": "string"
    }
  ],
  "metadata": "object"
}
```

**Data Extraction**:
- Retrieves all messages in conversation history
- Formats timestamps and message structure
- Includes session metadata

---

### 6. POST `/memory/test`
**Purpose**: Test memory functionality

**Response Format**:
```json
{
  "status": "string",
  "test_results": "object",
  "performance": "object"
}
```

**Data Processing**:
- Performs memory system tests
- Validates memory operations
- Returns test results and performance metrics

---

### 7. POST `/memory/test-prompt`
**Purpose**: Test prompt processing with memory

**Response Format**:
```json
{
  "prompt": "string",
  "response": "string",
  "memory_used": "boolean",
  "context": "string"
}
```

**Data Processing**:
- Tests prompt processing with memory integration
- Shows if memory was used in response generation
- Returns context information

---

### 8. GET `/memory/debug`
**Purpose**: Get debug information for memory system

**Response Format**:
```json
{
  "memory_status": "object",
  "configuration": "object",
  "errors": "array",
  "performance": "object"
}
```

**Data Extraction**:
- Provides detailed memory system status
- Shows configuration settings
- Lists any errors or issues
- Includes performance metrics

---

## Health Endpoints

### 9. GET `/health`
**Purpose**: Basic health check

**Response Format**:
```json
{
  "status": "string",
  "message": "string",
  "timestamp": "string"
}
```

**Data Processing**:
- Checks basic system availability
- Returns simple status response

---

### 10. GET `/health/system`
**Purpose**: Get detailed system health information

**Response Format**:
```json
{
  "status": "string",
  "services": {
    "rag_service": "string",
    "llm_client": "string",
    "retriever": "string",
    "memory": "string"
  },
  "version": "string",
  "timestamp": "string"
}
```

**Data Extraction**:
- Checks all system components
- Validates service connectivity
- Returns comprehensive health status

---

### 11. GET `/health/performance`
**Purpose**: Get performance statistics

**Response Format**:
```json
{
  "llm_health": "object",
  "memory_stats": "object",
  "performance_metrics": "object",
  "system_resources": "object"
}
```

**Data Processing**:
- Collects LLM client health status
- Gathers memory usage statistics
- Calculates performance metrics
- Monitors system resources

---

### 12. POST `/health/reset`
**Purpose**: Reset system state

**Response Format**:
```json
{
  "status": "string",
  "reset_components": "array",
  "timestamp": "string"
}
```

**Data Processing**:
- Resets system components
- Clears caches and temporary data
- Returns reset confirmation

---

### 13. GET `/health/debug`
**Purpose**: Get debug information

**Response Format**:
```json
{
  "system_info": "object",
  "configuration": "object",
  "logs": "array",
  "errors": "array"
}
```

**Data Extraction**:
- Provides system information
- Shows configuration details
- Returns recent logs
- Lists any errors

---

## Data Formatting & Validation

### Input Validation
- **Query Length**: 1-1000 characters
- **Session ID**: Optional, max 50 characters
- **Top K**: Integer between 1-100
- **Retrieval Method**: Must be one of: `title_first`, `multi`, `hybrid`, `semantic`

### Data Sanitization
- Removes potentially malicious content
- Truncates strings to safe lengths
- Validates data types and formats
- Escapes special characters

## Context Extraction & Product Processing

### Context Extraction Process
1. **Stream Chunk Processing**: 
   - Receives streaming chunks from API endpoints
   - Processes "token" chunks for real-time display
   - Extracts context from "complete" chunk type

2. **Product Data Extraction**:
   ```python
   def extract_products_from_context(context: str) -> List[Dict]:
       # Parses context for product information
       # Extracts Title, Price, and Image URLs
       # Returns structured product data
   ```

3. **Data Cleaning Functions**:
   - `clean_product_title()`: Removes prefixes, sanitizes text
   - `clean_product_price()`: Formats prices with currency symbols
   - URL sanitization for product images

4. **Session State Management**:
   - Stores extracted products in `st.session_state.products`
   - Maintains last 10 products for display
   - Updates product gallery in sidebar

### Product Data Structure
```json
{
  "title": "Cleaned product title",
  "price": "Formatted price (e.g., $29.99)",
  "image": "Sanitized image URL"
}
```

### Context Parsing Patterns
- **Title Extraction**: `Title[:\s]+([^\n]+)`
- **Price Extraction**: `Price[:\s]+([^\n]+)`
- **Image URL Extraction**: `https?://[^\s<>\"]+\.(?:jpg|jpeg|png|gif|webp)`

### Response Formatting
- Consistent JSON structure
- Proper error handling
- Metadata inclusion
- Timestamp formatting

### Error Handling
- HTTP status codes (400, 500, etc.)
- Structured error messages
- Validation error details
- Network error handling

---

## API Client Usage

### Synchronous Requests
```python
# Create API client
api_client = create_api_client()

# Send chat message
response = await api_client.send_chat_message(
    query="Your question here",
    session_id="session_123",
    top_k=5,
    retrieval_method="title_first"
)
```

### Streaming Requests
```python
# Stream chat response
async for chunk in api_client.send_chat_message_stream(
    query="Your question here",
    session_id="session_123"
):
    print(chunk)
```

### Context Manager Usage
```python
async with create_api_client_context() as client:
    response = await client.send_chat_message("Your question")
```

---

## Authentication & Security
- Input validation and sanitization
- Rate limiting (configured per endpoint)
- Error handling without exposing sensitive information
- Session management for conversation continuity

---

## Performance Considerations
- Connection pooling for HTTP requests
- Async/await for non-blocking operations
- Streaming responses for real-time interaction
- Memory management for session data
- Caching for frequently accessed data 