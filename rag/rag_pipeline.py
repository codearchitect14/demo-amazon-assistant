import logging
from typing import List, Dict, Any, Optional
import numpy as np
from rag.retriever import MultiVectorRetriever
from rag.advanced_retriever import AdvancedMultiVectorRetriever, RetrievalConfig
from rag.advanced_prompts import AdvancedPromptEngineer, AdvancedPromptConfig
from rag.evaluation import RAGEvaluator, EvaluationConfig
from rag.performance_optimizer import PerformanceOptimizer, PerformanceConfig
from app.config import Config
from rag.rag_utils import (
    llm_client,
    ConversationMemory,
    RedisConversationMemory,
    LangChainConversationMemory,
    logger,
    # Business logic functions
    run_rag_pipeline_sync,
    run_rag_pipeline_async as run_rag_pipeline_async_standalone,
    get_system_health_sync,
    get_system_health_async,
)


def convert_numpy_types(obj):
    """Convert numpy types to Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class RAGPipeline:
    """
    High-level RAG pipeline: orchestrates retrieval and answer generation
    """

    def __init__(
        self,
        qdrant_url: str = Config.QDRANT_URL,
        qdrant_api_key: Optional[str] = Config.QDRANT_API_KEY,
        embedding_model: str = Config.EMBEDDING_MODEL,
        enable_memory: bool = Config.MEMORY_ENABLED,
        memory_type: str = "auto",
    ):

        # Initialize retriever based on configuration
        if Config.ENABLE_HYBRID_SEARCH:
            # Use advanced retriever with hybrid search
            retrieval_config = RetrievalConfig(
                method="hybrid" if Config.ENABLE_HYBRID_SEARCH else "dense",
                enable_cross_encoder=Config.ENABLE_CROSS_ENCODER,
                enable_reranking=Config.ENABLE_RERANKING,
                enable_query_expansion=Config.ENABLE_QUERY_EXPANSION,
                cross_encoder_model=Config.CROSS_ENCODER_MODEL,
            )
            self.retriever = AdvancedMultiVectorRetriever(
                qdrant_url=qdrant_url,
                qdrant_api_key=qdrant_api_key,
                embedding_model=embedding_model,
                config=retrieval_config,
            )
            logger.info("Initialized advanced retriever with hybrid search")
        else:
            # Use basic retriever
            self.retriever = MultiVectorRetriever(
                qdrant_url=qdrant_url,
                qdrant_api_key=qdrant_api_key,
                embedding_model=embedding_model,
            )
            logger.info("Initialized basic retriever")

        # Initialize LLM client
        self.llm_client = llm_client
        self.model = Config.GROQ_PRIMARY_MODEL

        # Initialize memory based on type
        if enable_memory:
            if memory_type == "langchain":
                self.memory = LangChainConversationMemory()
                logger.info("Using LangChain conversation buffer memory")
            elif memory_type == "redis" and Config.REDIS_ENABLED:
                self.memory = RedisConversationMemory()
                logger.info("Using Redis-based conversation memory")
            elif memory_type == "in_memory":
                self.memory = ConversationMemory()
                logger.info("Using in-memory conversation storage")
            else:
                # Auto-select: Redis if available, otherwise LangChain, fallback to in-memory
                if Config.REDIS_ENABLED:
                    self.memory = RedisConversationMemory()
                    logger.info("Using Redis-based conversation memory (auto-selected)")
                else:
                    self.memory = LangChainConversationMemory()
                    logger.info(
                        "Using LangChain conversation buffer memory (auto-selected)"
                    )
        else:
            self.memory = None
            logger.info("Memory disabled")

        self.memory_enabled = enable_memory
        self.memory_type = memory_type

        # Initialize advanced components
        self._initialize_advanced_components()

    def _initialize_advanced_components(self):
        """Initialize advanced components based on configuration"""

        # Initialize prompt engineer
        if Config.ENABLE_STRUCTURED_PROMPTS:
            prompt_config = AdvancedPromptConfig(
                reasoning_type="chain_of_thought",
                enable_structured_output=True,
                enable_confidence_scoring=True,
                enable_source_citation=True,
                enable_uncertainty_handling=True,
            )
            self.prompt_engineer = AdvancedPromptEngineer(config=prompt_config)
            logger.info("Initialized advanced prompt engineer")
        else:
            self.prompt_engineer = None

        # Initialize evaluator
        if Config.ENABLE_EVALUATION:
            evaluation_config = EvaluationConfig(
                enable_relevance_scoring=True,
                enable_accuracy_checking=True,
                enable_hallucination_detection=True,
                enable_source_verification=True,
                enable_response_time_tracking=True,
                relevance_threshold=Config.RELEVANCE_THRESHOLD,
                accuracy_threshold=Config.ACCURACY_THRESHOLD,
                hallucination_threshold=Config.HALLUCINATION_THRESHOLD,
            )
            self.evaluator = RAGEvaluator(config=evaluation_config)
            logger.info("Initialized RAG evaluator")
        else:
            self.evaluator = None

        # Initialize performance optimizer
        if Config.ENABLE_PERFORMANCE_OPTIMIZATION:
            performance_config = PerformanceConfig(
                enable_caching=True,
                enable_batching=True,
                enable_parallel_processing=True,
                cache_ttl=Config.CACHE_TTL,
                batch_size=Config.BATCH_SIZE,
                max_workers=Config.MAX_WORKERS,
                enable_async_processing=True,
            )
            self.performance_optimizer = PerformanceOptimizer(config=performance_config)
            logger.info("Initialized performance optimizer")
        else:
            self.performance_optimizer = None

    def run_rag_pipeline(
        self,
        question: str,
        session_id: str = None,
        top_k: int = None,
        retrieval_method: str = "title_first",
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve context and generate answer with memory support.
        """
        return run_rag_pipeline_sync(
            retriever=self.retriever,
            llm_client=self.llm_client,
            memory=self.memory,
            memory_enabled=self.memory_enabled,
            model=self.model,
            question=question,
            session_id=session_id,
            top_k=top_k,
            retrieval_method=retrieval_method,
        )

    async def run_rag_pipeline_async(
        self,
        question: str,
        session_id: str = None,
        top_k: int = None,
        retrieval_method: str = "title_first",
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve context and generate answer with memory support (async).
        """
        return await run_rag_pipeline_async_standalone(
            retriever=self.retriever,
            llm_client=self.llm_client,
            memory=self.memory,
            memory_enabled=self.memory_enabled,
            model=self.model,
            question=question,
            session_id=session_id,
            top_k=top_k,
            retrieval_method=retrieval_method,
        )

    async def run_advanced_rag_pipeline(
        self,
        question: str,
        session_id: str = None,
        top_k: int = None,
        retrieval_method: str = "title_first",
    ) -> Dict[str, Any]:
        """
        Advanced RAG pipeline with all features enabled.
        """
        import time

        start_time = time.time()

        # Get conversation history
        conversation_history = ""
        if self.memory_enabled and session_id and self.memory:
            try:
                conversation_history = await self.memory.get_conversation_summary_async(
                    session_id
                )
            except Exception as e:
                logger.warning(f"Error getting conversation history: {e}")

        # Use advanced retriever if available
        if hasattr(self.retriever, "advanced_search"):
            search_result = await self.retriever.advanced_search(
                query=question,
                session_id=session_id,
                conversation_history=conversation_history,
            )
            context = self._format_advanced_search_results(search_result)
        else:
            # Fallback to basic retrieval
            from rag.rag_utils import retrieve_context_async

            context = await retrieve_context_async(
                retriever=self.retriever,
                query=question,
                top_k=top_k,
                retrieval_method=retrieval_method,
            )

        # Use advanced prompts if available
        if self.prompt_engineer:
            system_prompt = self.prompt_engineer.build_advanced_prompt(
                context=context,
                question=question,
                conversation_history=conversation_history,
            )
            user_prompt = f"Question: {question}\n\nContext: {context}"
        else:
            # Fallback to basic prompts
            from prompts import get_rag_system_prompt, build_rag_user_prompt

            system_prompt = get_rag_system_prompt()
            user_prompt = build_rag_user_prompt(
                context=context,
                question=question,
                conversation_history=conversation_history,
            )

        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.llm_client.generate_response_async(messages)

        # Parse structured response if using advanced prompts
        parsed_response = None
        if self.prompt_engineer:
            parsed_response = self.prompt_engineer.parse_structured_response(response)

        # Store in memory
        if self.memory_enabled and session_id and self.memory:
            await self.memory.add_interaction_async(
                session_id=session_id,
                question=question,
                answer=response,
                context=context,
                metadata={
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                    "model": self.model,
                    "advanced_features": True,
                },
            )

        # Evaluate response if evaluator is available
        evaluation_result = None
        if self.evaluator:
            response_time = time.time() - start_time
            evaluation_result = self.evaluator.evaluate_rag_response(
                query=question,
                context=context,
                response=response,
                response_time=response_time,
            )
            # Convert numpy types for JSON serialization
            evaluation_result = convert_numpy_types(evaluation_result)

        # Prepare result
        result = {
            "question": question,
            "answer": (
                parsed_response.get("final_answer", response)
                if parsed_response
                else response
            ),
            "context": context,
            "metadata": {
                "memory_enabled": self.memory_enabled,
                "has_conversation_history": bool(conversation_history),
                "retrieval_method": retrieval_method,
                "session_id": session_id,
                "model": self.model,
                "advanced_features": True,
                "parsed_response": parsed_response,
                "evaluation": evaluation_result,
            },
        }

        return result

    def _format_advanced_search_results(self, search_result: Dict[str, Any]) -> str:
        """Format advanced search results for LLM context"""
        if not search_result.get("documents"):
            return ""

        formatted_docs = []
        for doc in search_result["documents"]:
            content = doc.page_content
            metadata = doc.metadata

            # Add metadata if available
            if metadata:
                metadata_str = " | ".join(
                    [f"{k}: {v}" for k, v in metadata.items() if k != "text"]
                )
                if metadata_str:
                    content = f"{content} [{metadata_str}]"

            formatted_docs.append(content)

        return "\n\n".join(formatted_docs)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if self.memory:
            return self.memory.get_memory_stats()
        return {"enabled": False, "error": "Memory not initialized"}

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        """Get memory usage statistics (async)"""
        if self.memory:
            return await self.memory.get_memory_stats_async()
        return {"enabled": False, "error": "Memory not initialized"}

    def clear_session_memory(self, session_id: str):
        """Clear conversation history for a specific session"""
        if self.memory:
            self.memory.clear_session(session_id)

    async def clear_session_memory_async(self, session_id: str):
        """Clear conversation history for a specific session (async)"""
        if self.memory:
            await self.memory.clear_session_async(session_id)

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        if self.memory:
            return self.memory.get_recent_context(session_id)
        return []

    async def get_conversation_history_async(
        self, session_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session (async)"""
        if self.memory:
            return await self.memory.get_recent_context_async(session_id)
        return []

    def get_llm_health_status(self) -> Dict[str, Any]:
        """Get LLM client health status"""
        if hasattr(self, "llm_client") and self.llm_client:
            return self.llm_client.get_health_status()
        return {"error": "LLM client not initialized"}

    async def get_llm_health_status_async(self) -> Dict[str, Any]:
        """Get LLM client health status (async)"""
        if hasattr(self, "llm_client") and self.llm_client:
            return await self.llm_client.get_health_status_async()
        return {"error": "LLM client not initialized"}

    def reset_llm_health(self):
        """Reset LLM client health status"""
        if hasattr(self, "llm_client") and self.llm_client:
            self.llm_client.reset_health()
            logger.info("LLM client health status reset")

    async def reset_llm_health_async(self):
        """Reset LLM client health status (async)"""
        if hasattr(self, "llm_client") and self.llm_client:
            await self.llm_client.reset_health_async()
            logger.info("LLM client health status reset")

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        return get_system_health_sync(
            memory=self.memory,
            memory_enabled=self.memory_enabled,
            model=self.model,
            retriever=self.retriever,
            llm_client=self.llm_client,
        )

    async def get_system_health_async(self) -> Dict[str, Any]:
        """Get comprehensive system health status (async)"""
        return await get_system_health_async(
            memory=self.memory,
            memory_enabled=self.memory_enabled,
            model=self.model,
            retriever=self.retriever,
            llm_client=self.llm_client,
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {
            "advanced_features": {
                "hybrid_search": Config.ENABLE_HYBRID_SEARCH,
                "cross_encoder": Config.ENABLE_CROSS_ENCODER,
                "query_expansion": Config.ENABLE_QUERY_EXPANSION,
                "reranking": Config.ENABLE_RERANKING,
                "evaluation": Config.ENABLE_EVALUATION,
                "performance_optimization": Config.ENABLE_PERFORMANCE_OPTIMIZATION,
                "structured_prompts": Config.ENABLE_STRUCTURED_PROMPTS,
            }
        }

        if self.performance_optimizer:
            stats["performance"] = self.performance_optimizer.get_performance_stats()

        return stats


# Convenience function for backward compatibility
def run_rag_pipeline(
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "title_first",
    memory_type: str = "auto",
) -> Dict[str, Any]:
    """Complete RAG pipeline: retrieve context and generate answer with optional memory support."""
    pipeline = RAGPipeline(memory_type=memory_type)
    return pipeline.run_rag_pipeline(question, session_id, top_k, retrieval_method)


# Async convenience function
async def run_rag_pipeline_async(
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "title_first",
    memory_type: str = "auto",
) -> Dict[str, Any]:
    """Complete RAG pipeline: retrieve context and generate answer with optional memory support (async)."""
    pipeline = RAGPipeline(memory_type=memory_type)
    return await pipeline.run_rag_pipeline_async(
        question, session_id, top_k, retrieval_method
    )


# Example usage and testing
if __name__ == "__main__":
    import uuid

    logger.info("Starting RAG pipeline testing with advanced features")

    # Test with advanced features enabled
    pipeline = RAGPipeline(enable_memory=True, memory_type="langchain")
    session_id = str(uuid.uuid4())

    # Test conversation flow
    conversation_questions = [
        "What are some good wireless headphones?",
        "Which of those have the best battery life?",
        "What about noise cancellation features?",
    ]

    print(f"Session ID: {session_id}")

    for i, question in enumerate(conversation_questions, 1):
        print(f"\n{'='*60}")
        print(f"CONVERSATION TURN {i}: {question}")
        print(f"{'='*60}")

        try:
            result = pipeline.run_rag_pipeline(
                question=question, session_id=session_id, retrieval_method="title_first"
            )

            print(f"\nQUESTION: {result['question']}")
            print(f"\nANSWER: {result['answer'][:300]}...")
            print(
                f"\nMEMORY ENABLED: {result['metadata'].get('memory_enabled', False)}"
            )
            print(
                f"HAS CONVERSATION HISTORY: {result['metadata'].get('has_conversation_history', False)}"
            )

            if result.get("conversation_history"):
                print(
                    f"\nCONVERSATION HISTORY: {result['conversation_history'][:200]}..."
                )

        except Exception as e:
            logger.error(f"Error testing question {i}: {e}")
            print(f"Error: {e}")

    # Show final memory stats
    print(f"\n{'='*60}")
    print("FINAL MEMORY STATS")
    print(f"{'='*60}")
    memory_stats = pipeline.get_memory_stats()
    for key, value in memory_stats.items():
        print(f"{key}: {value}")

    # Show system health status
    print(f"\n{'='*60}")
    print("SYSTEM HEALTH STATUS")
    print(f"{'='*60}")
    health_status = pipeline.get_system_health()
    for component, status in health_status.items():
        print(f"\n{component.upper()}:")
        if isinstance(status, dict):
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {status}")

    # Show performance stats
    print(f"\n{'='*60}")
    print("PERFORMANCE STATS")
    print(f"{'='*60}")
    performance_stats = pipeline.get_performance_stats()
    for key, value in performance_stats.items():
        print(f"\n{key.upper()}:")
        if isinstance(value, dict):
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"  {value}")

    logger.info("RAG pipeline testing completed")
