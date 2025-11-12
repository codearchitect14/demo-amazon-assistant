# Rich Logging System for RAG Pipeline

## Overview

The rich logging system provides comprehensive, visually appealing logging for the RAG pipeline with detailed token tracking and optimization monitoring. It shows exactly what's being sent to the LLM and tracks token usage at every step.

## Features

### 🎯 **Real-time Token Tracking**
- Counts tokens for each component (system prompt, history, context, question)
- Shows token breakdown with percentages
- Tracks optimization savings

### 📊 **Visual Progress Indicators**
- Rich tables and panels for easy reading
- Progress spinners for pipeline steps
- Color-coded information

### 🔍 **Detailed LLM Input Analysis**
- Shows exactly what's sent to the LLM
- Breaks down each component with token counts
- Displays content previews

### 💾 **Memory Operation Tracking**
- Tracks token savings from context optimization
- Shows memory usage and interaction sizes
- Monitors optimization impact

### 🤖 **Agent Decision Transparency**
- Shows agent decisions with reasoning
- Color-coded decision types
- Confidence levels and rationale

## Installation

```bash
# Install required packages
pip install rich tiktoken

# Or update requirements.txt and install
pip install -r requirements.txt
```

## Usage

### Basic Setup

```python
from rich_logging import (
    log_pipeline_step, log_token_breakdown, log_prompt_analysis,
    log_memory_operation, log_agent_decision, log_final_summary,
    log_what_sent_to_llm, count_tokens
)

# Count tokens in text
tokens = count_tokens("Your text here")
print(f"Tokens: {tokens}")
```

### Pipeline Step Logging

```python
# Log pipeline steps with progress indicators
log_pipeline_step("Pipeline Start", session_id, {
    "question_length": 45,
    "memory_enabled": True,
    "retrieval_method": "multi",
    "model": "llama3-8b-8192"
})
```

### Token Breakdown

```python
# Show detailed token breakdown
token_data = {
    "system_prompt": 150,
    "conversation_history": 300,
    "retrieved_context": 800,
    "user_question": 50
}
log_token_breakdown("RAG Pipeline Token Usage", token_data)
```

### Prompt Analysis

```python
# Analyze what's being sent to LLM
prompt_data = {
    "conversation_only": False,
    "system_tokens": 150,
    "history_tokens": 300,
    "context_tokens": 800,
    "question_tokens": 50,
    "system_content": "You are a helpful AI assistant...",
    "history_content": "Previous conversation...",
    "context_content": "Product information...",
    "question_content": "What are the specs?",
    "savings_from_optimization": 0
}
log_prompt_analysis(session_id, prompt_data)
```

### Agent Decision Logging

```python
# Log agent decisions with reasoning
log_agent_decision(session_id, "retrieve", {
    "confidence": "high",
    "rationale": "User asked about specific product features"
})
```

### Memory Operation Tracking

```python
# Track memory operations and savings
log_memory_operation("Add Interaction", session_id, {
    "interaction_size_bytes": 1024,
    "session_size_bytes": 5120,
    "total_interactions": 5,
    "context_saved_bytes": 5000,
    "context_saved_tokens": 1250,
    "processing_time_ms": 23.5
})
```

### What's Sent to LLM

```python
# Show exactly what's sent to LLM
prompt_components = {
    "content": {
        "system_prompt": "You are a helpful AI assistant...",
        "conversation_history": "Previous conversation context...",
        "retrieved_context": "Product information and specifications...",
        "user_question": "What are the specs of the MacBook Pro?"
    },
    "tokens": {
        "system_prompt": 150,
        "conversation_history": 300,
        "retrieved_context": 800,
        "user_question": 50
    }
}
log_what_sent_to_llm(session_id, prompt_components)
```

### Final Summary

```python
# Log final pipeline summary
summary_data = {
    "total_time_ms": 1250.5,
    "retrieval_performed": True,
    "conversation_only_mode": False,
    "input_tokens": 1300,
    "output_tokens": 200,
    "context_tokens": 800,
    "history_tokens": 300,
    "system_tokens": 150,
    "question_tokens": 50,
    "savings_from_optimization": 1200
}
log_final_summary(session_id, summary_data)
```

## Integration with RAG Pipeline

The rich logging is automatically integrated into the RAG pipeline. You'll see:

### 1. **Pipeline Start**
```
⠸ Pipeline Start - Complete
╭─────────────────────────────────────── 📋 Pipeline Start Details ────────────────────────────────────────╮
│ Question Length: 45                                                                                      │
│ Memory Enabled: True                                                                                     │
│ Retrieval Method: multi                                                                                  │
│ Model: llama3-8b-8192                                                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### 2. **Agent Decision**
```
╭─────────────────────────────────────────── 🤖 Agent Decision ────────────────────────────────────────────╮
│ Decision: RETRIEVE                                                                                       │
│ Confidence: high                                                                                         │
│ Rationale: User asked about specific product features that require new information retrieval             │
│ Session: test_session_123                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### 3. **Token Breakdown**
```
                🔍 RAG Pipeline Token Usage                 
╭──────────────────────┬──────────┬───────────┬────────────╮
│ Component            │ Length   │ Tokens    │ Percentage │
├──────────────────────┼──────────┼───────────┼────────────┤
│ System Prompt        │ 13 chars │ 150       │ 11.5%      │
│ Conversation History │ 20 chars │ 300       │ 23.1%      │
│ Retrieved Context    │ 17 chars │ 800       │ 61.5%      │
│ User Question        │ 13 chars │ 50        │ 3.8%       │
│                      │          │           │            │
│ **TOTAL**            │          │ **1,300** │ **100%**   │
╰──────────────────────┴──────────┴───────────┴────────────╯
```

### 4. **LLM Input Analysis**
```
╭───────────────────────────────────────── 🤖 LLM Prompt Analysis ─────────────────────────────────────────╮
│ Session: test_session_123                                                                                │
│ Mode: RAG with Context                                                                                   │
│ Timestamp: 13:51:19                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### 5. **Memory Operation**
```
╭────────────────────────────────────────── 💾 Memory Operation ───────────────────────────────────────────╮
│ Operation: Add Interaction                                                                               │
│ Session: test_session_123                                                                                │
│ Context Saved: 0 chars (0 tokens)                                                                        │
│ Interaction Size: 1,024 bytes                                                                            │
│ Optimization: Context excluded from memory                                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### 6. **Final Summary**
```
                                 📊 Pipeline Summary                                  
╭───────────────────────────┬────────────────────────┬───────────────────────────────╮
│ Metric                    │ Value                  │ Details                       │
├───────────────────────────┼────────────────────────┼───────────────────────────────┤
│ Total Time Ms             │ 1250.5                 │ milliseconds                  │
│ Retrieval Performed       │ True                   │                               │
│ Conversation Only Mode    │ False                  │                               │
│ Input Tokens              │ 1,300                  │ tokens                        │
│ Output Tokens             │ 200                    │ tokens                        │
│ Context Tokens            │ 800                    │ tokens                        │
│ History Tokens            │ 300                    │ tokens                        │
│ System Tokens             │ 150                    │ tokens                        │
│ Question Tokens           │ 50                     │ tokens                        │
│ Savings From Optimization │ 1200                   │                               │
│                           │                        │                               │
│ **Optimization Impact**   │ **1,200 tokens saved** │ context excluded from history │
╰───────────────────────────┴────────────────────────┴───────────────────────────────╯
```

## Configuration

### Rich Logger Configuration

```python
from rich_logging import RichLogger

# Create custom logger instance
logger = RichLogger(
    enable_rich=True,      # Enable rich formatting
    log_to_file=True,      # Also log to file
    log_file="rag_pipeline.log"
)
```

### Token Counting Configuration

The system uses `tiktoken` for accurate token counting:

```python
# Uses GPT-4 tokenizer by default
tokens = count_tokens("Your text here")

# Fallback to character-based estimation if tiktoken not available
# 1 token ≈ 4 characters
```

## Monitoring and Analysis

### Real-time Monitoring

The rich logging provides real-time visibility into:

1. **Token Usage**: See exactly how many tokens each component uses
2. **Optimization Impact**: Track savings from context optimization
3. **Pipeline Performance**: Monitor processing times
4. **Agent Decisions**: Understand why the agent makes certain decisions
5. **Memory Operations**: Track memory usage and savings

### Log Analysis

You can analyze the logs to:

- **Identify Token Bottlenecks**: See which components use the most tokens
- **Optimize Context Usage**: Understand how context affects token usage
- **Monitor Agent Performance**: Track agent decision patterns
- **Measure Optimization Impact**: Quantify savings from context optimization

### Example Analysis

```python
# Analyze token usage patterns
def analyze_token_usage(logs):
    total_tokens = 0
    context_tokens = 0
    history_tokens = 0
    
    for log in logs:
        if "input_tokens" in log:
            total_tokens += log["input_tokens"]
            context_tokens += log.get("context_tokens", 0)
            history_tokens += log.get("history_tokens", 0)
    
    print(f"Average tokens per request: {total_tokens / len(logs)}")
    print(f"Context usage: {context_tokens / total_tokens * 100:.1f}%")
    print(f"History usage: {history_tokens / total_tokens * 100:.1f}%")
```

## Benefits

### 🚀 **Performance Monitoring**
- Real-time token tracking
- Processing time monitoring
- Memory usage optimization

### 🔍 **Debugging and Analysis**
- Detailed breakdown of what's sent to LLM
- Agent decision transparency
- Optimization impact visualization

### 💡 **Optimization Insights**
- Token usage patterns
- Context optimization savings
- Memory efficiency tracking

### 📊 **Visual Clarity**
- Rich tables and panels
- Color-coded information
- Progress indicators

## Testing

Run the test script to see the rich logging in action:

```bash
python test_rich_logging.py
```

This will demonstrate all the logging features with realistic RAG pipeline data.

## Troubleshooting

### Common Issues

1. **Missing tiktoken**: Falls back to character-based estimation
2. **Rich not installed**: Install with `pip install rich`
3. **Console compatibility**: Rich works in most terminals

### Debug Mode

Enable debug logging for more detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Conclusion

The rich logging system provides comprehensive visibility into the RAG pipeline, making it easy to:

- **Track token usage** at every step
- **Monitor optimization impact** from context removal
- **Understand agent decisions** with reasoning
- **Analyze performance** with detailed metrics
- **Debug issues** with clear visual feedback

This system helps you optimize your RAG pipeline and understand exactly what's happening under the hood! 🎯 