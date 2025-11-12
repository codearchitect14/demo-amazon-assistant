#!/usr/bin/env python3
"""
Test script to verify LLM fallback mechanism is working correctly.
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import Config
from rag.rag_utils import LLMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def test_llm_client_initialization():
    """Test LLM client initialization with different configurations."""
    print("\n=== Testing LLM Client Initialization ===")
    
    # Test 1: With fallback API key
    print("\n1. Testing with fallback API key...")
    try:
        client = LLMClient(
            primary_api_key=Config.GROQ_API_KEY,
            primary_model=Config.GROQ_PRIMARY_MODEL,
            fallback_api_key=Config.GROQ_FALLBACK_API_KEY,
            fallback_model=Config.GROQ_FALLBACK_MODEL,
        )
        print(f"✓ Client initialized successfully")
        print(f"  Primary client available: {client.primary_client is not None}")
        print(f"  Fallback client available: {client.fallback_client is not None}")
        print(f"  Primary async client available: {client.primary_client_async is not None}")
        print(f"  Fallback async client available: {client.fallback_client_async is not None}")
        
        health = client.get_health_status()
        print(f"  Health status: {health}")
        
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
    
    # Test 2: Without fallback API key
    print("\n2. Testing without fallback API key...")
    try:
        client = LLMClient(
            primary_api_key=Config.GROQ_API_KEY,
            primary_model=Config.GROQ_PRIMARY_MODEL,
            fallback_api_key=None,
            fallback_model=Config.GROQ_FALLBACK_MODEL,
        )
        print(f"✓ Client initialized successfully")
        print(f"  Primary client available: {client.primary_client is not None}")
        print(f"  Fallback client available: {client.fallback_client is not None}")
        print(f"  Primary async client available: {client.primary_client_async is not None}")
        print(f"  Fallback async client available: {client.fallback_client_async is not None}")
        
        health = client.get_health_status()
        print(f"  Health status: {health}")
        
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")

async def test_llm_fallback_async():
    """Test async LLM fallback mechanism."""
    print("\n=== Testing Async LLM Fallback ===")
    
    try:
        client = LLMClient(
            primary_api_key=Config.GROQ_API_KEY,
            primary_model=Config.GROQ_PRIMARY_MODEL,
            fallback_api_key=Config.GROQ_FALLBACK_API_KEY,
            fallback_model=Config.GROQ_FALLBACK_MODEL,
        )
        
        messages = [
            {"role": "user", "content": "Hello, this is a test message. Please respond with 'Test successful'."}
        ]
        
        print("\nTesting async response generation...")
        response = await client.generate_response_async(messages)
        print(f"✓ Response received: {response[:100]}...")
        
        # Test health status
        health = await client.get_health_status_async()
        print(f"✓ Health status: {health}")
        
    except Exception as e:
        print(f"✗ Async test failed: {e}")

def test_llm_fallback_sync():
    """Test synchronous LLM fallback mechanism."""
    print("\n=== Testing Sync LLM Fallback ===")
    
    try:
        client = LLMClient(
            primary_api_key=Config.GROQ_API_KEY,
            primary_model=Config.GROQ_PRIMARY_MODEL,
            fallback_api_key=Config.GROQ_FALLBACK_API_KEY,
            fallback_model=Config.GROQ_FALLBACK_MODEL,
        )
        
        messages = [
            {"role": "user", "content": "Hello, this is a test message. Please respond with 'Test successful'."}
        ]
        
        print("\nTesting sync response generation...")
        response = client.generate_response(messages)
        print(f"✓ Response received: {response[:100]}...")
        
        # Test health status
        health = client.get_health_status()
        print(f"✓ Health status: {health}")
        
    except Exception as e:
        print(f"✗ Sync test failed: {e}")

def test_configuration():
    """Test configuration values."""
    print("\n=== Testing Configuration ===")
    
    print(f"Primary API Key: {'✓ Set' if Config.GROQ_API_KEY else '✗ Not set'}")
    print(f"Primary Model: {Config.GROQ_PRIMARY_MODEL}")
    print(f"Fallback API Key: {'✓ Set' if Config.GROQ_FALLBACK_API_KEY else '✗ Not set'}")
    print(f"Fallback Model: {Config.GROQ_FALLBACK_MODEL}")
    print(f"Circuit Breaker Enabled: {Config.ENABLE_CIRCUIT_BREAKER}")
    print(f"Retry Logic Enabled: {Config.ENABLE_RETRY_LOGIC}")

async def main():
    """Main test function."""
    print("🧪 LLM Fallback Mechanism Test")
    print("=" * 50)
    
    # Test configuration
    test_configuration()
    
    # Test client initialization
    test_llm_client_initialization()
    
    # Test sync fallback
    test_llm_fallback_sync()
    
    # Test async fallback
    await test_llm_fallback_async()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 