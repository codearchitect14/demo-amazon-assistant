"""
RAG pipeline orchestration utilities.
"""

import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PipelineOrchestrator(ABC):
    """
    Abstract base class for RAG pipeline orchestration.
    """
    
    @abstractmethod
    def run_pipeline_sync(self, **kwargs) -> Dict[str, Any]:
        """Run pipeline synchronously."""
        pass
    
    @abstractmethod
    async def run_pipeline_async(self, **kwargs) -> Dict[str, Any]:
        """Run pipeline asynchronously."""
        pass


class RAGPipelineOrchestrator(PipelineOrchestrator):
    """
    RAG pipeline orchestration implementation.
    """
    
    def run_pipeline_sync(
        self,
        retriever,
        llm_client,
        memory,
        memory_enabled: bool,
        model: str,
        question: str,
        session_id: str = None,
        top_k: int = None,
        retrieval_method: str = "multi",
    ) -> Dict[str, Any]:
        """
        Run RAG pipeline synchronously.
        
        Args:
            retriever: Retriever instance
            llm_client: LLM client instance
            memory: Memory instance
            memory_enabled: Whether memory is enabled
            model: Model name
            question: User question
            session_id: Session identifier
            top_k: Number of documents to retrieve
            retrieval_method: Retrieval method
            
        Returns:
            Pipeline result dictionary
        """
        try:
            logger.info(f"Running RAG pipeline sync for session: {session_id}")
            start_time = time.time()
            
            # Get conversation history
            conversation_history = ""
            if memory_enabled and memory and session_id:
                try:
                    recent_context = memory.get_recent_context(session_id)
                    if recent_context:
                        conversation_history = "\n".join([
                            f"Q: {entry['question']}\nA: {entry['answer']}"
                            for entry in recent_context
                        ])
                except Exception as e:
                    logger.warning(f"Error getting conversation history: {e}")
            
            # Retrieve context
            from rag.utils.business_logic import retrieve_context_sync
            context = retrieve_context_sync(retriever, question, top_k, retrieval_method)
            
            # Generate answer
            from rag.utils.business_logic import generate_answer_sync
            answer = generate_answer_sync(
                llm_client, context, question, session_id, conversation_history
            )
            
            # Store in memory if enabled
            if memory_enabled and memory and session_id:
                try:
                    memory.add_interaction(
                        session_id=session_id,
                        question=question,
                        answer=answer,
                        context=context,
                        metadata={
                            "model": model,
                            "retrieval_method": retrieval_method,
                            "top_k": top_k,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Error storing in memory: {e}")
            
            processing_time = time.time() - start_time
            
            return {
                "question": question,
                "answer": answer,
                "context": context,
                "metadata": {
                    "processing_time": processing_time,
                    "model": model,
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                    "memory_enabled": memory_enabled,
                    "has_conversation_history": bool(conversation_history),
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline sync: {e}")
            return {
                "question": question,
                "answer": "I apologize, but I encountered an error while processing your request. Please try again.",
                "context": "",
                "metadata": {
                    "error": str(e),
                    "memory_enabled": memory_enabled,
                    "has_conversation_history": False,
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                }
            }
    
    async def run_pipeline_async(
        self,
        retriever,
        llm_client,
        memory,
        memory_enabled: bool,
        model: str,
        question: str,
        session_id: str = None,
        top_k: int = None,
        retrieval_method: str = "multi",
    ) -> Dict[str, Any]:
        """
        Run RAG pipeline asynchronously.
        
        Args:
            retriever: Retriever instance
            llm_client: LLM client instance
            memory: Memory instance
            memory_enabled: Whether memory is enabled
            model: Model name
            question: User question
            session_id: Session identifier
            top_k: Number of documents to retrieve
            retrieval_method: Retrieval method
            
        Returns:
            Pipeline result dictionary
        """
        try:
            logger.info(f"Running RAG pipeline async for session: {session_id}")
            start_time = time.time()
            
            # Get conversation history
            conversation_history = ""
            if memory_enabled and memory and session_id:
                try:
                    recent_context = await memory.get_recent_context_async(session_id)
                    if recent_context:
                        conversation_history = "\n".join([
                            f"Q: {entry['question']}\nA: {entry['answer']}"
                            for entry in recent_context
                        ])
                except Exception as e:
                    logger.warning(f"Error getting conversation history: {e}")
            
            # Retrieve context
            from rag.utils.business_logic import retrieve_context_async
            context = await retrieve_context_async(retriever, question, top_k, retrieval_method)
            
            # Generate answer
            from rag.utils.business_logic import generate_answer_async
            answer = await generate_answer_async(
                llm_client, context, question, session_id, conversation_history
            )
            
            # Store in memory if enabled
            if memory_enabled and memory and session_id:
                try:
                    await memory.add_interaction_async(
                        session_id=session_id,
                        question=question,
                        answer=answer,
                        context=context,
                        metadata={
                            "model": model,
                            "retrieval_method": retrieval_method,
                            "top_k": top_k,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Error storing in memory: {e}")
            
            processing_time = time.time() - start_time
            
            return {
                "question": question,
                "answer": answer,
                "context": context,
                "metadata": {
                    "processing_time": processing_time,
                    "model": model,
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                    "memory_enabled": memory_enabled,
                    "has_conversation_history": bool(conversation_history),
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline async: {e}")
            return {
                "question": question,
                "answer": "I apologize, but I encountered an error while processing your request. Please try again.",
                "context": "",
                "metadata": {
                    "error": str(e),
                    "memory_enabled": memory_enabled,
                    "has_conversation_history": False,
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                }
            }


def run_rag_pipeline_sync(
    retriever,
    llm_client,
    memory,
    memory_enabled: bool,
    model: str,
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "multi",
) -> Dict[str, Any]:
    """
    Run RAG pipeline synchronously.
    
    Args:
        retriever: Retriever instance
        llm_client: LLM client instance
        memory: Memory instance
        memory_enabled: Whether memory is enabled
        model: Model name
        question: User question
        session_id: Session identifier
        top_k: Number of documents to retrieve
        retrieval_method: Retrieval method
        
    Returns:
        Pipeline result dictionary
    """
    orchestrator = RAGPipelineOrchestrator()
    return orchestrator.run_pipeline_sync(
        retriever=retriever,
        llm_client=llm_client,
        memory=memory,
        memory_enabled=memory_enabled,
        model=model,
        question=question,
        session_id=session_id,
        top_k=top_k,
        retrieval_method=retrieval_method,
    )


async def run_rag_pipeline_async(
    retriever,
    llm_client,
    memory,
    memory_enabled: bool,
    model: str,
    question: str,
    session_id: str = None,
    top_k: int = None,
    retrieval_method: str = "multi",
) -> Dict[str, Any]:
    """
    Run RAG pipeline asynchronously.
    
    Args:
        retriever: Retriever instance
        llm_client: LLM client instance
        memory: Memory instance
        memory_enabled: Whether memory is enabled
        model: Model name
        question: User question
        session_id: Session identifier
        top_k: Number of documents to retrieve
        retrieval_method: Retrieval method
        
    Returns:
        Pipeline result dictionary
    """
    orchestrator = RAGPipelineOrchestrator()
    return await orchestrator.run_pipeline_async(
        retriever=retriever,
        llm_client=llm_client,
        memory=memory,
        memory_enabled=memory_enabled,
        model=model,
        question=question,
        session_id=session_id,
        top_k=top_k,
        retrieval_method=retrieval_method,
    ) 