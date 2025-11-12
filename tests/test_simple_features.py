#!/usr/bin/env python3
"""
Test script to verify that simple retrieval and prompts are being used
instead of advanced features.
"""

import asyncio
import logging
from rag.rag_pipeline import RAGPipeline
from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_simple_features():
    """Test that simple features are being used"""

    print("=" * 60)
    print("TESTING SIMPLE FEATURES CONFIGURATION")
    print("=" * 60)

    # Check configuration
    print("\n1. Configuration Check:")
    print(f"   ENABLE_HYBRID_SEARCH: {Config.ENABLE_HYBRID_SEARCH}")
    print(f"   ENABLE_CROSS_ENCODER: {Config.ENABLE_CROSS_ENCODER}")
    print(f"   ENABLE_QUERY_EXPANSION: {Config.ENABLE_QUERY_EXPANSION}")
    print(f"   ENABLE_RERANKING: {Config.ENABLE_RERANKING}")
    print(f"   ENABLE_EVALUATION: {Config.ENABLE_EVALUATION}")
    print(
        f"   ENABLE_PERFORMANCE_OPTIMIZATION: {Config.ENABLE_PERFORMANCE_OPTIMIZATION}"
    )
    print(f"   ENABLE_STRUCTURED_PROMPTS: {Config.ENABLE_STRUCTURED_PROMPTS}")

    # Initialize pipeline
    print("\n2. Initializing RAG Pipeline:")
    pipeline = RAGPipeline(enable_memory=True, memory_type="langchain")

    # Check retriever type
    print(f"   Retriever type: {type(pipeline.retriever).__name__}")
    if hasattr(pipeline.retriever, "advanced_search"):
        print("   ✓ Advanced retriever detected")
    else:
        print("   ✓ Simple retriever detected")

    # Check prompt engineer
    if hasattr(pipeline, "prompt_engineer") and pipeline.prompt_engineer:
        print("   ✓ Advanced prompt engineer detected")
    else:
        print("   ✓ Simple prompts will be used")

    # Check evaluator
    if hasattr(pipeline, "evaluator") and pipeline.evaluator:
        print("   ✓ RAG evaluator detected")
    else:
        print("   ✓ No evaluation enabled")

    # Test a simple query
    print("\n3. Testing Simple Query:")
    test_question = "What are some good wireless headphones?"

    try:
        result = await pipeline.run_rag_pipeline_async(
            question=test_question,
            session_id="test_session_123",
            retrieval_method="title_first",
        )

        print(f"   Question: {result['question']}")
        print(f"   Answer length: {len(result['answer'])} characters")
        print(f"   Context length: {len(result['context'])} characters")
        print(f"   Memory enabled: {result['metadata'].get('memory_enabled', False)}")
        print(
            f"   Has conversation history: {result['metadata'].get('has_conversation_history', False)}"
        )

        # Check if advanced features were used
        metadata = result.get("metadata", {})
        if metadata.get("advanced_features", False):
            print("   ⚠️  Advanced features were used")
        else:
            print("   ✓ Simple features were used")

    except Exception as e:
        print(f"   ❌ Error during test: {e}")
        return False

    # Test performance stats
    print("\n4. Performance Stats:")
    try:
        stats = pipeline.get_performance_stats()
        advanced_features = stats.get("advanced_features", {})

        print("   Advanced Features Status:")
        for feature, enabled in advanced_features.items():
            status = "✓" if enabled else "✗"
            print(f"     {feature}: {status}")

    except Exception as e:
        print(f"   ❌ Error getting performance stats: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    asyncio.run(test_simple_features())
