#!/usr/bin/env python3
"""
Test script to verify the refactored structure works correctly.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_shared_utilities():
    """Test shared utilities functionality."""
    print("\n=== Testing Shared Utilities ===")
    
    try:
        from shared.utils.serialization import serialize_for_json, NumpySerializer
        import numpy as np
        
        # Test numpy serialization
        test_data = {
            "integer": np.int32(42),
            "float": np.float64(3.14),
            "array": np.array([1, 2, 3]),
            "boolean": np.bool_(True),
            "nested": {
                "array": np.array([4, 5, 6])
            }
        }
        
        serialized = serialize_for_json(test_data)
        print("✓ Numpy serialization works")
        
        # Test error handling
        from shared.utils.error_handling import safe_execute, RAGException
        
        def test_function():
            return "success"
        
        result = safe_execute(test_function, fallback_value="fallback")
        assert result == "success"
        print("✓ Error handling utilities work")
        
        return True
        
    except Exception as e:
        print(f"✗ Shared utilities test failed: {e}")
        return False


async def test_resilience_components():
    """Test resilience components functionality."""
    print("\n=== Testing Resilience Components ===")
    
    try:
        from rag.resilience.circuit_breaker import CircuitBreaker
        from rag.resilience.retry_handler import RetryHandler
        
        # Test circuit breaker
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def success_func():
            return "success"
        
        def failure_func():
            raise Exception("test failure")
        
        # Test success
        result = cb.call(success_func)
        assert result == "success"
        print("✓ Circuit breaker success handling works")
        
        # Test retry handler
        rh = RetryHandler(max_retries=2, base_delay=0.1)
        
        def retry_success_func():
            return "retry success"
        
        result = rh.call_with_retry(retry_success_func)
        assert result == "retry success"
        print("✓ Retry handler works")
        
        return True
        
    except Exception as e:
        print(f"✗ Resilience components test failed: {e}")
        return False


async def test_llm_client():
    """Test LLM client functionality."""
    print("\n=== Testing LLM Client ===")
    
    try:
        from rag.llm.client import LLMClient
        from app.config import Config
        
        # Test client initialization
        client = LLMClient(
            primary_api_key=Config.GROQ_API_KEY,
            primary_model=Config.GROQ_PRIMARY_MODEL,
            enable_circuit_breaker=False,
            enable_retry=False
        )
        
        # Test health status
        health = client.get_health_status()
        assert "primary" in health
        print("✓ LLM client initialization works")
        
        return True
        
    except Exception as e:
        print(f"✗ LLM client test failed: {e}")
        return False


async def test_memory_components():
    """Test memory components functionality."""
    print("\n=== Testing Memory Components ===")
    
    try:
        from rag.memory.base import MemoryStrategy, MemoryFactory
        from rag.memory.conversation import ConversationMemory
        
        # Test memory factory
        memory = MemoryFactory.create_memory("in_memory")
        assert isinstance(memory, MemoryStrategy)
        print("✓ Memory factory works")
        
        # Test conversation memory
        conv_memory = ConversationMemory()
        
        # Test adding interaction
        conv_memory.add_interaction(
            session_id="test_session",
            question="What is this?",
            answer="This is a test."
        )
        
        # Test getting recent context
        context = conv_memory.get_recent_context("test_session")
        assert len(context) == 1
        assert context[0]["question"] == "What is this?"
        print("✓ Conversation memory works")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory components test failed: {e}")
        return False


async def test_business_logic():
    """Test business logic utilities."""
    print("\n=== Testing Business Logic ===")
    
    try:
        from rag.utils.business_logic import format_retrieved_context
        
        # Test context formatting
        test_docs = [
            {
                "page_content": "Test content 1",
                "metadata": {"title": "Test Product", "price": 99.99}
            },
            {
                "page_content": "Test content 2",
                "metadata": {"title": "Another Product", "rating": 4.5}
            }
        ]
        
        formatted = format_retrieved_context(test_docs)
        assert "Test content 1" in formatted
        assert "Test content 2" in formatted
        print("✓ Business logic utilities work")
        
        return True
        
    except Exception as e:
        print(f"✗ Business logic test failed: {e}")
        return False


async def test_dependency_injection():
    """Test dependency injection container."""
    print("\n=== Testing Dependency Injection ===")
    
    try:
        from core.container import get_container, reset_container
        
        # Test container initialization
        container = get_container()
        assert container is not None
        print("✓ Container initialization works")
        
        # Test service registration
        registered_services = container.get_registered_services()
        assert "singletons" in registered_services
        print("✓ Service registration works")
        
        # Test container reset
        reset_container()
        print("✓ Container reset works")
        
        return True
        
    except Exception as e:
        print(f"✗ Dependency injection test failed: {e}")
        return False


async def test_api_structure():
    """Test API structure and routes."""
    print("\n=== Testing API Structure ===")
    
    try:
        from app.api.routes.chat import ChatRequest, ChatResponse
        from app.api.routes.memory import router as memory_router
        from app.api.routes.health import router as health_router
        
        # Test request/response models
        chat_request = ChatRequest(
            query="test query",
            top_k=5,
            retrieval_method="title_first"
        )
        assert chat_request.query == "test query"
        print("✓ API models work")
        
        # Test router inclusion
        assert memory_router is not None
        assert health_router is not None
        print("✓ API routes structure works")
        
        return True
        
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False


async def test_service_layer():
    """Test service layer functionality."""
    print("\n=== Testing Service Layer ===")
    
    try:
        from app.services.rag_service import RAGService
        
        # Test service initialization
        service = RAGService()
        assert service is not None
        print("✓ Service layer initialization works")
        
        return True
        
    except Exception as e:
        print(f"✗ Service layer test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting Refactored Structure Tests")
    print("=" * 50)
    
    tests = [
        ("Shared Utilities", test_shared_utilities),
        ("Resilience Components", test_resilience_components),
        ("LLM Client", test_llm_client),
        ("Memory Components", test_memory_components),
        ("Business Logic", test_business_logic),
        ("Dependency Injection", test_dependency_injection),
        ("API Structure", test_api_structure),
        ("Service Layer", test_service_layer),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Report results
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactored structure is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 