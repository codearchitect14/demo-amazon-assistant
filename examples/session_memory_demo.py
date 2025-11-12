#!/usr/bin/env python3
"""
Session Memory Demo
Demonstrates how memory works across different users and page refreshes.
"""

import os
import sys
import time
import uuid

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.rag_pipeline import RAGPipeline


def demo_session_memory():
    """Demonstrate session memory behavior"""
    print("=" * 60)
    print("SESSION MEMORY DEMONSTRATION")
    print("=" * 60)

    # Create RAG pipeline with memory enabled
    pipeline = RAGPipeline(enable_memory=True)

    # Simulate different users
    user1_session = "user_123"
    user2_session = "user_456"

    print(f"\n1. USER 1 SESSION: {user1_session}")
    print("-" * 40)

    # User 1's first question
    result1 = pipeline.run_rag_pipeline(
        question="What are good wireless headphones?", session_id=user1_session
    )
    print(f"Q1: {result1['question']}")
    print(f"A1: {result1['answer'][:100]}...")
    print(f"Memory enabled: {result1['metadata']['memory_enabled']}")
    print(f"Has history: {result1['metadata']['has_conversation_history']}")

    # User 1's follow-up question (should have context)
    result2 = pipeline.run_rag_pipeline(
        question="Which of those have the best battery life?", session_id=user1_session
    )
    print(f"\nQ2: {result2['question']}")
    print(f"A2: {result2['answer'][:100]}...")
    print(f"Has history: {result2['metadata']['has_conversation_history']}")

    print(f"\n2. USER 2 SESSION: {user2_session}")
    print("-" * 40)

    # User 2's first question (should be fresh, no history)
    result3 = pipeline.run_rag_pipeline(
        question="What are good gaming laptops?", session_id=user2_session
    )
    print(f"Q1: {result3['question']}")
    print(f"A1: {result3['answer'][:100]}...")
    print(f"Has history: {result3['metadata']['has_conversation_history']}")

    print(f"\n3. PAGE REFRESH SIMULATION")
    print("-" * 40)

    # Simulate page refresh - use same session ID
    print("Simulating page refresh for User 1...")
    result4 = pipeline.run_rag_pipeline(
        question="What about noise cancellation?",
        session_id=user1_session,  # Same session ID
    )
    print(f"Q3 (after refresh): {result4['question']}")
    print(f"A3: {result4['answer'][:100]}...")
    print(f"Has history: {result4['metadata']['has_conversation_history']}")

    print(f"\n4. MEMORY STATISTICS")
    print("-" * 40)

    # Get memory stats
    memory_stats = pipeline.get_memory_stats()
    print("Memory Statistics:")
    for key, value in memory_stats.items():
        print(f"  {key}: {value}")

    print(f"\n5. SESSION COMPARISON")
    print("-" * 40)

    # Show that sessions are isolated
    user1_history = pipeline.get_conversation_history(user1_session)
    user2_history = pipeline.get_conversation_history(user2_session)

    print(f"User 1 ({user1_session}) interactions: {len(user1_history)}")
    print(f"User 2 ({user2_session}) interactions: {len(user2_history)}")

    print(f"\n6. CLEARING SESSION")
    print("-" * 40)

    # Clear one session
    pipeline.clear_session_memory(user1_session)
    print(f"Cleared memory for {user1_session}")

    # Check if cleared
    user1_history_after = pipeline.get_conversation_history(user1_session)
    print(f"User 1 interactions after clear: {len(user1_history_after)}")

    print(f"\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)


def demo_memory_persistence():
    """Demonstrate memory persistence across different scenarios"""
    print(f"\n" + "=" * 60)
    print("MEMORY PERSISTENCE DEMONSTRATION")
    print("=" * 60)

    pipeline = RAGPipeline(enable_memory=True)
    session_id = "demo_session"

    # First interaction
    print("1. First interaction...")
    result1 = pipeline.run_rag_pipeline(
        question="What are good headphones?", session_id=session_id
    )
    print(f"Question: {result1['question']}")
    print(f"Has history: {result1['metadata']['has_conversation_history']}")

    # Simulate "page refresh" - same session ID
    print("\n2. Simulating page refresh (same session ID)...")
    result2 = pipeline.run_rag_pipeline(
        question="Which ones have noise cancellation?",
        session_id=session_id,  # Same session ID = memory persists
    )
    print(f"Question: {result2['question']}")
    print(f"Has history: {result2['metadata']['has_conversation_history']}")

    # Simulate "new user" - different session ID
    print("\n3. Simulating new user (different session ID)...")
    result3 = pipeline.run_rag_pipeline(
        question="What are good laptops?",
        session_id="new_user_session",  # Different session ID = fresh start
    )
    print(f"Question: {result3['question']}")
    print(f"Has history: {result3['metadata']['has_conversation_history']}")

    print(f"\n" + "=" * 60)
    print("PERSISTENCE DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    print("Session Memory Behavior Demonstration")
    print("This shows how memory works with different users and page refreshes.")

    demo_session_memory()
    demo_memory_persistence()

    print("\nKey Points:")
    print("✅ Memory persists across page refreshes (same session ID)")
    print("✅ Each user has separate memory (different session ID)")
    print("✅ Memory is server-side, not browser-side")
    print("✅ Redis memory persists across server restarts")
    print("✅ In-memory storage is lost on server restart")
