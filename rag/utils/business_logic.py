"""
Business logic utilities for RAG pipeline operations.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from app.config import Config
from prompts import get_rag_system_prompt, build_rag_user_prompt
from shared.utils.serialization import serialize_for_json

logger = logging.getLogger(__name__)


def format_field_value(field_name: str, value: Any) -> str:
    """
    Format a field value for display in context.
    
    Args:
        field_name: Name of the field
        value: Value to format
        
    Returns:
        Formatted field value string
    """
    if value is None:
        return ""
    
    if isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return value.strip()
    elif isinstance(value, list):
        if len(value) == 0:
            return ""
        elif len(value) == 1:
            return str(value[0])
        else:
            return ", ".join(str(item) for item in value[:3]) + (
                f" and {len(value) - 3} more" if len(value) > 3 else ""
            )
    elif isinstance(value, dict):
        # For nested dictionaries, extract key information
        if "name" in value:
            return str(value["name"])
        elif "title" in value:
            return str(value["title"])
        else:
            return str(value)
    else:
        return str(value)


def format_retrieved_context(documents: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents into a context string for the LLM.
    
    Args:
        documents: List of retrieved documents
        
    Returns:
        Formatted context string
    """
    if not documents:
        return "No relevant information found."
    
    context_parts = []
    
    for i, doc in enumerate(documents, 1):
        if not doc or not doc.get("page_content"):
            continue
            
        content = doc["page_content"].strip()
        metadata = doc.get("metadata", {})
        
        # Format metadata fields
        metadata_parts = []
        for key, value in metadata.items():
            if key in ["source", "title", "brand", "price", "rating", "category"]:
                formatted_value = format_field_value(key, value)
                if formatted_value:
                    metadata_parts.append(f"{key.title()}: {formatted_value}")
        
        # Create document entry
        doc_entry = f"Document {i}:\n"
        if metadata_parts:
            doc_entry += "Metadata: " + " | ".join(metadata_parts) + "\n"
        doc_entry += f"Content: {content}\n"
        
        context_parts.append(doc_entry)
    
    if not context_parts:
        return "No relevant information found."
    
    return "\n".join(context_parts)


async def format_retrieved_context_async(documents: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents into a context string asynchronously.
    
    Args:
        documents: List of retrieved documents
        
    Returns:
        Formatted context string
    """
    import asyncio
    return await asyncio.to_thread(format_retrieved_context, documents)


def retrieve_context_sync(
    retriever, query: str, top_k: int = None, retrieval_method: str = "multi"
) -> str:
    """
    Retrieve context synchronously using the specified retriever.
    
    Args:
        retriever: Retriever instance
        query: Search query
        top_k: Number of documents to retrieve
        retrieval_method: Method to use for retrieval
        
    Returns:
        Formatted context string
    """
    try:
        logger.info(f"Retrieving context for query: {query}")
        start_time = time.time()
        
        if retrieval_method == "title_first":
            # Use title-first search for product-focused queries
            result = retriever.title_first_search(query, top_products=top_k or 5)
            
            # Check if we got results
            if not result.get("results"):
                logger.warning("No results found in title_first_search")
                return "No relevant product information found."
            
            # Format the results for LLM consumption
            formatted_context = retriever.format_product_data_for_llm(result["results"])
            logger.info(f"Title-first search completed in {time.time() - start_time:.2f}s")
            return formatted_context
        else:
            # Use standard search methods
            if hasattr(retriever, "search_titles"):
                title_docs = retriever.search_titles(query, k=top_k or 5)
            else:
                title_docs = []
            
            if hasattr(retriever, "search_reviews"):
                review_docs = retriever.search_reviews(query, k=top_k or 3)
            else:
                review_docs = []
            
            if hasattr(retriever, "search_qas"):
                qa_docs = retriever.search_qas(query, k=top_k or 3)
            else:
                qa_docs = []
            
            # Combine all documents
            all_docs = title_docs + review_docs + qa_docs
            
            # Format the context
            context = format_retrieved_context(all_docs)
            logger.info(f"Standard search completed in {time.time() - start_time:.2f}s")
            return context
            
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return "Error retrieving relevant information."


async def retrieve_context_async(
    retriever, query: str, top_k: int = None, retrieval_method: str = "multi"
) -> str:
    """
    Retrieve context asynchronously using the specified retriever.
    
    Args:
        retriever: Retriever instance
        query: Search query
        top_k: Number of documents to retrieve
        retrieval_method: Method to use for retrieval
        
    Returns:
        Formatted context string
    """
    import asyncio
    return await asyncio.to_thread(
        retrieve_context_sync, retriever, query, top_k, retrieval_method
    )


def generate_answer_sync(
    llm_client,
    context: str,
    question: str,
    session_id: str = None,
    conversation_history: str = "",
) -> str:
    """
    Generate answer synchronously using the LLM client.
    
    Args:
        llm_client: LLM client instance
        context: Retrieved context
        question: User question
        session_id: Session identifier
        conversation_history: Previous conversation history
        
    Returns:
        Generated answer
    """
    try:
        logger.info(f"Generating answer for session: {session_id}")
        start_time = time.time()
        
        # Build the prompt
        user_prompt = build_rag_user_prompt(context, question, conversation_history)
        system_prompt = get_rag_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Generate response
        response = llm_client.generate_response(messages)
        
        logger.info(f"Answer generation completed in {time.time() - start_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."


async def generate_answer_async(
    llm_client,
    context: str,
    question: str,
    session_id: str = None,
    conversation_history: str = "",
) -> str:
    """
    Generate answer asynchronously using the LLM client.
    
    Args:
        llm_client: LLM client instance
        context: Retrieved context
        question: User question
        session_id: Session identifier
        conversation_history: Previous conversation history
        
    Returns:
        Generated answer
    """
    try:
        logger.info(f"Generating answer asynchronously for session: {session_id}")
        start_time = time.time()
        
        # Build the prompt
        user_prompt = build_rag_user_prompt(context, question, conversation_history)
        system_prompt = get_rag_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        # Generate response
        response = await llm_client.generate_response_async(messages)
        
        logger.info(f"Async answer generation completed in {time.time() - start_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error generating answer asynchronously: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."


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
        retrieval_method: Method to use for retrieval
        
    Returns:
        Pipeline result dictionary
    """
    try:
        logger.info(f"Running RAG pipeline for session: {session_id}")
        start_time = time.time()
        
        # Get conversation history if memory is enabled
        conversation_history = ""
        if memory_enabled and session_id and memory:
            recent_context = memory.get_recent_context(session_id)
            if recent_context:
                conversation_history = "\n".join([
                    f"Q: {entry['question']}\nA: {entry['answer']}"
                    for entry in recent_context
                ])
        
        # Retrieve context
        context = retrieve_context_sync(retriever, question, top_k, retrieval_method)
        
        # Generate answer
        answer = generate_answer_sync(
            llm_client, context, question, session_id, conversation_history
        )
        
        # Store in memory if enabled
        if memory_enabled and session_id and memory:
            memory.add_interaction(session_id, question, answer, context)
        
        # Prepare result
        result = {
            "question": question,
            "answer": answer,
            "context": context,
            "metadata": {
                "memory_enabled": memory_enabled,
                "has_conversation_history": bool(conversation_history),
                "retrieval_method": retrieval_method,
                "top_k": top_k,
                "model": model,
                "processing_time": time.time() - start_time,
            }
        }
        
        logger.info(f"RAG pipeline completed in {time.time() - start_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Error in RAG pipeline: {e}")
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
                "model": model,
            }
        }


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
        retrieval_method: Method to use for retrieval
        
    Returns:
        Pipeline result dictionary
    """
    try:
        logger.info(f"Running async RAG pipeline for session: {session_id}")
        start_time = time.time()
        
        # Get conversation history if memory is enabled
        conversation_history = ""
        if memory_enabled and session_id and memory:
            recent_context = await memory.get_recent_context_async(session_id)
            if recent_context:
                conversation_history = "\n".join([
                    f"Q: {entry['question']}\nA: {entry['answer']}"
                    for entry in recent_context
                ])
        
        # Retrieve context
        context = await retrieve_context_async(retriever, question, top_k, retrieval_method)
        
        # Generate answer
        answer = await generate_answer_async(
            llm_client, context, question, session_id, conversation_history
        )
        
        # Store in memory if enabled
        if memory_enabled and session_id and memory:
            await memory.add_interaction_async(session_id, question, answer, context)
        
        # Prepare result
        result = {
            "question": question,
            "answer": answer,
            "context": context,
            "metadata": {
                "memory_enabled": memory_enabled,
                "has_conversation_history": bool(conversation_history),
                "retrieval_method": retrieval_method,
                "top_k": top_k,
                "model": model,
                "processing_time": time.time() - start_time,
            }
        }
        
        logger.info(f"Async RAG pipeline completed in {time.time() - start_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Error in async RAG pipeline: {e}")
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
                "model": model,
            }
        }


def get_system_health_sync(
    memory, memory_enabled: bool, model: str, retriever, llm_client
) -> Dict[str, Any]:
    """
    Get system health status synchronously.
    
    Args:
        memory: Memory instance
        memory_enabled: Whether memory is enabled
        model: Model name
        retriever: Retriever instance
        llm_client: LLM client instance
        
    Returns:
        System health status dictionary
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {}
        }
        
        # Check memory health
        if memory_enabled and memory:
            try:
                memory_stats = memory.get_memory_stats()
                health_status["components"]["memory"] = {
                    "status": "healthy",
                    "stats": memory_stats
                }
            except Exception as e:
                health_status["components"]["memory"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health_status["components"]["memory"] = {
                "status": "disabled"
            }
        
        # Check LLM health
        if llm_client:
            try:
                llm_health = llm_client.get_health_status()
                health_status["components"]["llm"] = {
                    "status": "healthy",
                    "health": llm_health
                }
            except Exception as e:
                health_status["components"]["llm"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Check retriever health
        if retriever:
            try:
                # Basic retriever health check
                health_status["components"]["retriever"] = {
                    "status": "healthy",
                    "type": type(retriever).__name__
                }
            except Exception as e:
                health_status["components"]["retriever"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Overall status
        unhealthy_components = [
            comp for comp in health_status["components"].values()
            if comp.get("status") == "unhealthy"
        ]
        
        if unhealthy_components:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


async def get_system_health_async(
    memory, memory_enabled: bool, model: str, retriever, llm_client
) -> Dict[str, Any]:
    """
    Get system health status asynchronously.
    
    Args:
        memory: Memory instance
        memory_enabled: Whether memory is enabled
        model: Model name
        retriever: Retriever instance
        llm_client: LLM client instance
        
    Returns:
        System health status dictionary
    """
    import asyncio
    return await asyncio.to_thread(
        get_system_health_sync, memory, memory_enabled, model, retriever, llm_client
    ) 