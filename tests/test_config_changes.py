#!/usr/bin/env python3
"""
Test script to verify configuration changes and retriever selection
"""

import asyncio
import logging
from rag.rag_pipeline import RAGPipeline
from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_configuration():
    """Test that the configuration is working correctly"""

    print("=" * 60)
    print("TESTING CONFIGURATION CHANGES")
    print("=" * 60)

    # Check current configuration
    print("\n1. Current Configuration:")
    print(f"   ENABLE_HYBRID_SEARCH: {Config.ENABLE_HYBRID_SEARCH}")
    print(f"   ENABLE_CROSS_ENCODER: {Config.ENABLE_CROSS_ENCODER}")
    print(f"   ENABLE_QUERY_EXPANSION: {Config.ENABLE_QUERY_EXPANSION}")
    print(f"   ENABLE_RERANKING: {Config.ENABLE_RERANKING}")
    print(f"   ENABLE_EVALUATION: {Config.ENABLE_EVALUATION}")
    print(
        f"   ENABLE_PERFORMANCE_OPTIMIZATION: {Config.ENABLE_PERFORMANCE_OPTIMIZATION}"
    )
    print(f"   ENABLE_STRUCTURED_PROMPTS: {Config.ENABLE_STRUCTURED_PROMPTS}")

    # Create a new pipeline instance
    print("\n2. Creating RAG Pipeline:")
    pipeline = RAGPipeline(enable_memory=True, memory_type="langchain")

    # Check retriever type
    retriever_type = type(pipeline.retriever).__name__
    print(f"   Retriever type: {retriever_type}")

    if retriever_type == "MultiVectorRetriever":
        print("   ✓ Using simple retriever")
    elif retriever_type == "AdvancedMultiVectorRetriever":
        print("   ⚠️  Using advanced retriever")
    else:
        print(f"   ❓ Unknown retriever type: {retriever_type}")

    # Check if advanced features are available
    print("\n3. Advanced Features Check:")
    has_advanced_search = hasattr(pipeline.retriever, "advanced_search")
    has_title_first_search = hasattr(pipeline.retriever, "title_first_search_async")
    has_prompt_engineer = (
        hasattr(pipeline, "prompt_engineer") and pipeline.prompt_engineer is not None
    )
    has_evaluator = hasattr(pipeline, "evaluator") and pipeline.evaluator is not None

    print(f"   Has advanced_search: {has_advanced_search}")
    print(f"   Has title_first_search_async: {has_title_first_search}")
    print(f"   Has prompt_engineer: {has_prompt_engineer}")
    print(f"   Has evaluator: {has_evaluator}")

    # Test a simple query
    print("\n4. Testing Simple Query:")
    test_question = "headphone"

    try:
        result = await pipeline.run_rag_pipeline_async(
            question=test_question,
            session_id="test_config_session",
            retrieval_method="title_first",
        )

        print(f"   Question: {result['question']}")
        print(f"   Answer length: {len(result['answer'])} characters")
        print(f"   Context length: {len(result['context'])} characters")
        print(f"   Success: ✓")

    except Exception as e:
        print(f"   ❌ Error during test: {e}")
        return False

    print("\n" + "=" * 60)
    print("CONFIGURATION TEST COMPLETED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    asyncio.run(test_configuration())
