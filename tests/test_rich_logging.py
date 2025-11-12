#!/usr/bin/env python3
"""
Test script for rich logging system with token tracking.
"""

import asyncio
import time
from rich_logging import (
    log_pipeline_step, log_token_breakdown, log_prompt_analysis,
    log_memory_operation, log_agent_decision, log_final_summary,
    log_what_sent_to_llm, log_context_optimization_impact, count_tokens
)


async def test_rich_logging():
    """Test the rich logging system with realistic RAG pipeline data."""
    
    print("🚀 Testing Rich Logging System")
    print("=" * 60)
    
    # Simulate session data
    session_id = "test_session_123"
    
    # Test 1: Pipeline steps
    print("\n1. Testing Pipeline Steps:")
    log_pipeline_step("Pipeline Start", session_id, {
        "question_length": 45,
        "memory_enabled": True,
        "retrieval_method": "multi",
        "model": "llama3-8b-8192"
    })
    
    log_pipeline_step("Conversation History Retrieved", session_id, {
        "conversation_length": 1200,
        "history_tokens": 300,
        "processing_time_ms": 45.2
    })
    
    # Test 2: Agent decision
    print("\n2. Testing Agent Decision:")
    log_agent_decision(session_id, "retrieve", {
        "confidence": "high",
        "rationale": "User asked about specific product features that require new information retrieval"
    })
    
    # Test 3: Token breakdown
    print("\n3. Testing Token Breakdown:")
    token_data = {
        "system_prompt": 150,
        "conversation_history": 300,
        "retrieved_context": 800,
        "user_question": 50
    }
    log_token_breakdown("RAG Pipeline Token Usage", token_data)
    
    # Test 4: Prompt analysis
    print("\n4. Testing Prompt Analysis:")
    prompt_data = {
        "conversation_only": False,
        "system_tokens": 150,
        "history_tokens": 300,
        "context_tokens": 800,
        "question_tokens": 50,
        "system_content": "You are a helpful AI assistant that provides accurate information about products...",
        "history_content": "Q: What are the best laptops?\nA: Here are some top recommendations...",
        "context_content": "Product: MacBook Pro 14-inch\nFeatures: M3 chip, 16GB RAM, 512GB SSD...",
        "question_content": "What are the specs of the MacBook Pro?",
        "savings_from_optimization": 0
    }
    log_prompt_analysis(session_id, prompt_data)
    
    # Test 5: Memory operation
    print("\n5. Testing Memory Operation:")
    log_memory_operation("Add Interaction", session_id, {
        "interaction_size_bytes": 1024,
        "session_size_bytes": 5120,
        "total_interactions": 5,
        "context_saved_bytes": 5000,
        "context_saved_tokens": 1250,
        "processing_time_ms": 23.5
    })
    
    # Test 6: What's sent to LLM
    print("\n6. Testing LLM Input Logging:")
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
    
    # Test 7: Context optimization impact
    print("\n7. Testing Context Optimization Impact:")
    before_optimization = {
        "total_tokens": 2500,
        "context_in_history": True,
        "memory_usage": "high"
    }
    after_optimization = {
        "total_tokens": 1300,
        "context_in_history": False,
        "memory_usage": "low"
    }
    log_context_optimization_impact(before_optimization, after_optimization)
    
    # Test 8: Final summary
    print("\n8. Testing Final Summary:")
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
    
    print("\n" + "=" * 60)
    print("✅ Rich logging tests completed!")
    print("=" * 60)


async def test_conversation_only_mode():
    """Test logging for conversation-only mode."""
    
    print("\n🧪 Testing Conversation-Only Mode")
    print("=" * 50)
    
    session_id = "conversation_session_456"
    
    # Agent decides to use conversation only
    log_agent_decision(session_id, "conversation", {
        "confidence": "medium",
        "rationale": "User's question can be answered using existing conversation history"
    })
    
    # Token breakdown for conversation-only mode
    token_data = {
        "system_prompt": 120,
        "conversation_history": 800,
        "user_question": 30
        # No retrieved context in conversation-only mode
    }
    log_token_breakdown("Conversation-Only Token Usage", token_data)
    
    # Prompt analysis for conversation-only mode
    prompt_data = {
        "conversation_only": True,
        "system_tokens": 120,
        "history_tokens": 800,
        "context_tokens": 0,  # No context
        "question_tokens": 30,
        "system_content": "You are a helpful AI assistant...",
        "history_content": "Extended conversation history with previous Q&A...",
        "question_content": "Can you remind me what we discussed?",
        "savings_from_optimization": 0
    }
    log_prompt_analysis(session_id, prompt_data)
    
    print("✅ Conversation-only mode tests completed!")


async def test_token_counting():
    """Test token counting functionality."""
    
    print("\n🔢 Testing Token Counting")
    print("=" * 40)
    
    test_texts = [
        "Hello, how are you?",
        "This is a longer text with more tokens to count.",
        "Product specifications: MacBook Pro 14-inch with M3 chip, 16GB RAM, 512GB SSD, Retina display with True Tone technology, Magic Keyboard with Touch ID, Force Touch trackpad, and Thunderbolt 4 ports.",
        "A very long text that contains many words and should result in a higher token count. This is useful for testing the token counting functionality of our rich logging system. We want to make sure that the token counting works correctly for various text lengths and content types.",
        ""  # Empty text
    ]
    
    for i, text in enumerate(test_texts, 1):
        tokens = count_tokens(text)
        print(f"Text {i}: {len(text)} chars → {tokens} tokens")
        if text:
            print(f"  Preview: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print()


async def main():
    """Run all rich logging tests."""
    
    print("🎯 Rich Logging System Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run tests
    await test_rich_logging()
    await test_conversation_only_mode()
    await test_token_counting()
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"🎉 All tests completed in {total_time:.2f} seconds!")
    print("=" * 60)
    
    print("\n📋 Test Summary:")
    print("✅ Pipeline step logging with progress indicators")
    print("✅ Agent decision logging with reasoning")
    print("✅ Token breakdown tables")
    print("✅ Prompt analysis with detailed breakdowns")
    print("✅ Memory operation tracking")
    print("✅ LLM input logging")
    print("✅ Context optimization impact visualization")
    print("✅ Final summary tables")
    print("✅ Token counting functionality")
    print("✅ Conversation-only mode logging")
    
    print("\n💡 The rich logging system provides:")
    print("   • Real-time token tracking")
    print("   • Visual progress indicators")
    print("   • Detailed breakdowns of what's sent to LLM")
    print("   • Optimization impact visualization")
    print("   • Memory usage tracking")
    print("   • Agent decision transparency")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 