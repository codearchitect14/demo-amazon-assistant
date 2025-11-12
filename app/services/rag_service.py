"""
RAG service layer for handling RAG pipeline operations.
"""

import logging
from typing import Dict, Any, Optional
from core.container import resolve_service
from core.config.adapter import get_configuration_manager
from rag.llm.client import LLMClient
from rag.retriever import MultiVectorRetriever
from rag.memory.base import MemoryStrategy
from rag.utils.business_logic import run_rag_pipeline_sync, run_rag_pipeline_async
from rag.utils.intent_recognition import IntentRecognitionService
from shared.utils.serialization import serialize_for_json

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service layer for RAG pipeline operations.
    
    This service encapsulates the business logic for RAG operations,
    separating it from API concerns and enabling easier testing.
    """

    def __init__(self):
        """Initialize RAG service with dependencies from container."""
        self.llm_client = resolve_service(LLMClient)
        self.retriever = resolve_service(MultiVectorRetriever)
        self.memory = resolve_service(MemoryStrategy)
        self.config_manager = get_configuration_manager()
        self.intent_service = IntentRecognitionService(self.llm_client)

    async def process_chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        retrieval_method: str = "title_first",
        use_advanced_features: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a chat request with intelligent intent recognition.
        
        Args:
            query: User query
            session_id: Session identifier
            top_k: Number of documents to retrieve
            retrieval_method: Method to use for retrieval
            use_advanced_features: Whether to use advanced features
            
        Returns:
            RAG pipeline result
        """
        try:
            logger.info(f"Processing chat request for session: {session_id}")
            
            # Get memory configuration
            memory_config = self.config_manager.get_memory_config()
            
            # Get conversation history for intent recognition
            conversation_history = ""
            if memory_config.enabled and session_id:
                recent_context = await self.memory.get_recent_context_async(session_id)
                if recent_context:
                    conversation_history = "\n".join([
                        f"Q: {entry['question']}\nA: {entry['answer']}"
                        for entry in recent_context
                    ])
            
            # Recognize intent
            intent_result = await self.intent_service.recognize_intent(
                query=query,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            logger.info(f"Intent recognized: {intent_result['intent_type']}, needs_retrieval: {intent_result['needs_retrieval']}")
            
            # Decide whether to retrieve or use conversation context
            if intent_result['needs_retrieval']:
                # Perform retrieval
                logger.info("Performing fresh retrieval based on intent")
                result = await self._process_with_retrieval(
                    query, session_id, top_k, retrieval_method, intent_result
                )
            else:
                # Use conversation context only
                logger.info("Using conversation context without retrieval")
                result = await self._process_without_retrieval(
                    query, session_id, conversation_history, intent_result
                )
            
            # Store in memory if enabled
            if memory_config.enabled and session_id:
                await self.memory.add_interaction_async(
                    session_id=session_id,
                    question=query,
                    answer=result.get("answer", ""),
                    context=result.get("context", ""),
                    metadata={
                        "intent_type": intent_result["intent_type"],
                        "needs_retrieval": intent_result["needs_retrieval"],
                        "confidence": intent_result["confidence"],
                        "retrieval_method": retrieval_method,
                        "top_k": top_k,
                    },
                )
            
            # Add intent information to result
            result["intent"] = intent_result
            
            # Serialize result for JSON response
            return serialize_for_json(result)
            
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            return {
                "question": query,
                "answer": "I apologize, but I encountered an error while processing your request. Please try again.",
                "context": "",
                "intent": {"intent_type": "ERROR", "needs_retrieval": False},
                "metadata": {
                    "error": str(e),
                    "memory_enabled": memory_config.enabled,
                    "has_conversation_history": False,
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                }
            }

    async def _process_with_retrieval(
        self, 
        query: str, 
        session_id: Optional[str], 
        top_k: int, 
        retrieval_method: str,
        intent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query with fresh retrieval."""
        # Get conversation history
        conversation_history = ""
        if self.config_manager.get_memory_config().enabled and session_id:
            recent_context = await self.memory.get_recent_context_async(session_id)
            if recent_context:
                conversation_history = "\n".join([
                    f"Q: {entry['question']}\nA: {entry['answer']}"
                    for entry in recent_context
                ])
        
        # Retrieve context
        from rag.utils.business_logic import retrieve_context_async
        context = await retrieve_context_async(
            self.retriever, query, top_k, retrieval_method
        )
        
        # Get appropriate system prompt
        system_prompt = self.intent_service.get_system_prompt_for_intent(
            intent_result["intent_type"], context
        )
        
        # Build user prompt
        from prompts import build_rag_user_prompt
        user_prompt = build_rag_user_prompt(context, query, conversation_history)
        
        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = await self.llm_client.generate_response_async(messages)
        
        return {
            "question": query,
            "answer": response,
            "context": context,
            "metadata": {
                "intent_type": intent_result["intent_type"],
                "needs_retrieval": True,
                "retrieval_method": retrieval_method,
                "top_k": top_k,
            }
        }

    async def _process_without_retrieval(
        self, 
        query: str, 
        session_id: Optional[str], 
        conversation_history: str,
        intent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query using only conversation context."""
        # Get conversation context from memory
        context = ""
        if self.config_manager.get_memory_config().enabled and session_id:
            recent_context = await self.memory.get_recent_context_async(session_id)
            if recent_context:
                # Get the most recent context
                latest_entry = recent_context[-1] if recent_context else {}
                context = latest_entry.get("context", "")
        
        # Get appropriate system prompt for conversation
        system_prompt = self.intent_service.get_system_prompt_for_intent(
            intent_result["intent_type"], context
        )
        
        # Build user prompt for conversation
        user_prompt = f"User Query: {query}\n\nPlease answer based on the available product information."
        
        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        response = await self.llm_client.generate_response_async(messages)
        
        return {
            "question": query,
            "answer": response,
            "context": context,
            "metadata": {
                "intent_type": intent_result["intent_type"],
                "needs_retrieval": False,
                "retrieval_method": "conversation_only",
                "top_k": 0,
            }
        }

    async def process_chat_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        retrieval_method: str = "title_first",
        use_advanced_features: bool = False,
    ):
        """
        Process a chat request with streaming response and intelligent intent recognition.
        
        Args:
            query: User query
            session_id: Session identifier
            top_k: Number of documents to retrieve
            retrieval_method: Method to use for retrieval
            use_advanced_features: Whether to use advanced features
            
        Yields:
            Streaming response chunks
        """
        try:
            logger.info(f"Processing streaming chat request for session: {session_id}")
            
            # Get conversation history for intent recognition
            conversation_history = ""
            if self.config_manager.get_memory_config().enabled and session_id:
                recent_context = await self.memory.get_recent_context_async(session_id)
                if recent_context:
                    conversation_history = "\n".join([
                        f"Q: {entry['question']}\nA: {entry['answer']}"
                        for entry in recent_context
                    ])
            
            # Recognize intent
            intent_result = await self.intent_service.recognize_intent(
                query=query,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            logger.info(f"Intent recognized: {intent_result['intent_type']}, needs_retrieval: {intent_result['needs_retrieval']}")
            
            # Decide whether to retrieve or use conversation context
            if intent_result['needs_retrieval']:
                # Perform retrieval
                logger.info("Performing fresh retrieval based on intent")
                async for chunk in self._process_stream_with_retrieval(
                    query, session_id, top_k, retrieval_method, intent_result
                ):
                    yield chunk
            else:
                # Use conversation context only
                logger.info("Using conversation context without retrieval")
                async for chunk in self._process_stream_without_retrieval(
                    query, session_id, conversation_history, intent_result
                ):
                    yield chunk
                
        except Exception as e:
            logger.error(f"Error processing streaming chat request: {e}")
            yield "I apologize, but I encountered an error while processing your request. Please try again."

    async def _process_stream_with_retrieval(
        self, 
        query: str, 
        session_id: Optional[str], 
        top_k: int, 
        retrieval_method: str,
        intent_result: Dict[str, Any]
    ):
        """Process query with streaming and fresh retrieval."""
        # Get conversation history
        conversation_history = ""
        if self.config_manager.get_memory_config().enabled and session_id:
            recent_context = await self.memory.get_recent_context_async(session_id)
            if recent_context:
                conversation_history = "\n".join([
                    f"Q: {entry['question']}\nA: {entry['answer']}"
                    for entry in recent_context
                ])
        
        # Retrieve context
        from rag.utils.business_logic import retrieve_context_async
        context = await retrieve_context_async(
            self.retriever, query, top_k, retrieval_method
        )
        
        logger.info(f"Retrieved context length: {len(context)}")
        logger.info(f"Context preview: {context[:200]}...")
        
        # Get appropriate system prompt
        system_prompt = self.intent_service.get_system_prompt_for_intent(
            intent_result["intent_type"], context
        )
        
        # Build user prompt
        from prompts import build_rag_user_prompt
        user_prompt = build_rag_user_prompt(context, query, conversation_history)
        
        # Stream response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        full_response = ""
        async for chunk in self.llm_client.generate_response_stream_async(messages):
            full_response += chunk
            yield chunk
        
        # Store in memory if enabled
        if self.config_manager.get_memory_config().enabled and session_id:
            await self.memory.add_interaction_async(
                session_id=session_id,
                question=query,
                answer=full_response,
                context=context,
                metadata={
                    "intent_type": intent_result["intent_type"],
                    "needs_retrieval": True,
                    "retrieval_method": retrieval_method,
                    "top_k": top_k,
                },
            )
        
        # Return context for frontend
        yield {"type": "context", "content": context, "intent": intent_result}

    async def _process_stream_without_retrieval(
        self, 
        query: str, 
        session_id: Optional[str], 
        conversation_history: str,
        intent_result: Dict[str, Any]
    ):
        """Process query with streaming using only conversation context."""
        # Get conversation context from memory
        context = ""
        if self.config_manager.get_memory_config().enabled and session_id:
            recent_context = await self.memory.get_recent_context_async(session_id)
            if recent_context:
                # Get the most recent context
                latest_entry = recent_context[-1] if recent_context else {}
                context = latest_entry.get("context", "")
        
        # Get appropriate system prompt for conversation
        system_prompt = self.intent_service.get_system_prompt_for_intent(
            intent_result["intent_type"], context
        )
        
        # Build user prompt for conversation
        user_prompt = f"User Query: {query}\n\nPlease answer based on the available product information."
        
        # Stream response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        full_response = ""
        async for chunk in self.llm_client.generate_response_stream_async(messages):
            full_response += chunk
            yield chunk
        
        # Store in memory if enabled
        if self.config_manager.get_memory_config().enabled and session_id:
            await self.memory.add_interaction_async(
                session_id=session_id,
                question=query,
                answer=full_response,
                context=context,
                metadata={
                    "intent_type": intent_result["intent_type"],
                    "needs_retrieval": False,
                    "retrieval_method": "conversation_only",
                    "top_k": 0,
                },
            )
        
        # Return context for frontend (might be empty for conversation-only)
        yield {"type": "context", "content": context, "intent": intent_result}

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Memory statistics dictionary
        """
        try:
            stats = await self.memory.get_memory_stats_async()
            return serialize_for_json(stats)
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    async def clear_session_memory(self, session_id: str) -> Dict[str, Any]:
        """
        Clear memory for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Operation result
        """
        try:
            await self.memory.clear_session_async(session_id)
            return {"success": True, "message": f"Memory cleared for session {session_id}"}
        except Exception as e:
            logger.error(f"Error clearing session memory: {e}")
            return {"success": False, "error": str(e)}

    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation history
        """
        try:
            recent_context = await self.memory.get_recent_context_async(session_id)
            return serialize_for_json({
                "session_id": session_id,
                "history": recent_context
            })
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return {"error": str(e)}

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Returns:
            System health information
        """
        try:
            from rag.utils.business_logic import get_system_health_async
            health = await get_system_health_async(
                self.memory,
                self.config_manager.get_memory_config().enabled,
                self.config_manager.get_llm_config().primary_model,
                self.retriever,
                self.llm_client
            )
            return serialize_for_json(health)
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"error": str(e)} 