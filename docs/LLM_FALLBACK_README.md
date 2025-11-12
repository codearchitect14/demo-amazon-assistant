# LLM Fallback Mechanism Fix

## Problem Description

The RAG demo application had an issue where the LLM fallback mechanism was not working correctly. The system was configured to use both a primary and secondary model, but when the primary model failed, it was not properly rolling back to the secondary model.

## Root Cause Analysis

### Issue 1: String "None" vs None Value
In the `LLMClient` initialization, the fallback API key was being set to the string `"None"` instead of the actual `None` value:

```python
# Before (incorrect)
fallback_api_key: str = "None",  # This is a string, not None

# After (correct)
fallback_api_key: str = None,  # This is the actual None value
```

### Issue 2: Improper Client Initialization
The client initialization logic was checking for the string `"None"` instead of properly handling `None` values:

```python
# Before (incorrect)
self.fallback_client = (
    Groq(api_key=fallback_api_key) if fallback_api_key != "None" else None
)

# After (correct)
self.fallback_client = (
    Groq(api_key=fallback_api_key) if fallback_api_key and fallback_api_key != "None" else None
)
```

### Issue 3: Missing Fallback API Key Validation
The fallback logic wasn't checking if the fallback API key was actually available before attempting to use the fallback model.

## Solution Implemented

### 1. Fixed Client Initialization
- Changed the default parameter from `"None"` to `None`
- Added proper validation for API keys before initializing clients
- Added better logging to show when fallback is configured

### 2. Improved Fallback Logic
- Added validation to check if fallback API key exists before attempting fallback
- Added informative logging when fallback is attempted
- Added logging when fallback is successful or when no fallback is available

### 3. Enhanced Configuration Handling
- Added proper handling of empty or None fallback API keys
- Added validation in the global LLM client initialization

## Configuration

### Environment Variables

To use the fallback mechanism, configure these environment variables in your `.env` file:

```bash
# Primary LLM Configuration
GROQ_API_KEY=your_primary_groq_api_key_here
GROQ_PRIMARY_MODEL=llama-3.3-70b-versatile

# Fallback LLM Configuration (Optional)
GROQ_FALLBACK_API_KEY=your_fallback_groq_api_key_here
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant

# Resilience Configuration
ENABLE_CIRCUIT_BREAKER=true
ENABLE_RETRY_LOGIC=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
```

### Configuration Options

1. **With Fallback**: Set both `GROQ_API_KEY` and `GROQ_FALLBACK_API_KEY`
2. **Without Fallback**: Set only `GROQ_API_KEY` (leave `GROQ_FALLBACK_API_KEY` empty or unset)

## How It Works

### 1. Primary Model Attempt
The system first attempts to use the primary model (`llama-3.3-70b-versatile` by default).

### 2. Fallback Trigger
If the primary model fails (due to API errors, rate limits, etc.), the system automatically attempts to use the fallback model.

### 3. Fallback Conditions
The fallback is triggered when:
- The primary model throws an exception
- The circuit breaker is open (too many failures)
- The primary model is unavailable

### 4. Fallback Model
The fallback model (`llama-3.1-8b-instant` by default) is a faster, smaller model that provides a backup when the primary model fails.

## Testing the Fix

### Run the Test Script
```bash
python test_llm_fallback.py
```

This script will:
1. Test client initialization with and without fallback
2. Test synchronous and asynchronous fallback mechanisms
3. Verify configuration values
4. Test actual API calls

### Expected Output
```
🧪 LLM Fallback Mechanism Test
==================================================

=== Testing Configuration ===
Primary API Key: ✓ Set
Primary Model: llama-3.3-70b-versatile
Fallback API Key: ✓ Set
Fallback Model: llama-3.1-8b-instant

=== Testing LLM Client Initialization ===
✓ Client initialized successfully
  Primary client available: True
  Fallback client available: True
  Health status: {...}

=== Testing Sync LLM Fallback ===
✓ Response received: Test successful...

=== Testing Async LLM Fallback ===
✓ Response received: Test successful...
```

## Logging

The system now provides detailed logging for fallback operations:

```
[INFO] LLM Client initialized with primary model: llama-3.3-70b-versatile
[INFO] Fallback model configured: llama-3.1-8b-instant
[WARNING] Primary model failed (1 failures): API error
[INFO] Attempting fallback to model: llama-3.1-8b-instant
[INFO] Successfully used fallback model
```

## Health Monitoring

You can monitor the health of both models:

```python
from rag.rag_utils import llm_client

# Get health status
health = llm_client.get_health_status()
print(health)

# Reset health metrics
llm_client.reset_health()
```

## Best Practices

1. **Always set a fallback API key** for production environments
2. **Use different API keys** for primary and fallback to avoid rate limit issues
3. **Monitor health metrics** to track model performance
4. **Test fallback scenarios** regularly
5. **Configure appropriate circuit breaker settings** for your use case

## Troubleshooting

### Issue: Fallback not working
- Check that `GROQ_FALLBACK_API_KEY` is set in your `.env` file
- Verify the fallback API key is valid
- Check logs for error messages

### Issue: Both models failing
- Verify both API keys are valid
- Check network connectivity
- Review circuit breaker settings

### Issue: No fallback attempted
- Ensure `GROQ_FALLBACK_API_KEY` is properly configured
- Check that the fallback model name is correct
- Review the logging for initialization messages

## Files Modified

- `rag/rag_utils.py`: Fixed LLM client initialization and fallback logic
- `test_llm_fallback.py`: Added test script for verification
- `LLM_FALLBACK_README.md`: This documentation file 