"""
Intent recognition for intelligent retrieval decisions.
"""

import logging
from typing import Dict, Any, Optional, List
from prompts import get_intent_recognition_system_prompt, get_conversation_system_prompt, get_enhanced_rag_system_prompt

logger = logging.getLogger(__name__)


class IntentRecognitionService:
    """
    Service for recognizing user intent and deciding retrieval strategy.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def recognize_intent(
        self, 
        query: str, 
        conversation_history: str = "",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize user intent and decide retrieval strategy.
        
        Args:
            query: User's current query
            conversation_history: Previous conversation context
            session_id: Session identifier
            
        Returns:
            Dict with intent type and metadata
        """
        try:
            logger.info(f"Recognizing intent for query: '{query}'")
            
            # Build intent recognition prompt
            system_prompt = get_intent_recognition_system_prompt()
            
            # Include conversation history if available
            if conversation_history:
                user_prompt = f"""Conversation History:
{conversation_history}

Current Query: {query}

Determine the intent of the current query."""
            else:
                user_prompt = f"Current Query: {query}\n\nDetermine the intent of this query."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Get intent from LLM
            intent_response = await self.llm_client.generate_response_async(messages)
            intent_type = self._parse_intent_response(intent_response)
            
            logger.info(f"Recognized intent: {intent_type} for query: '{query}'")
            
            return {
                "intent_type": intent_type,
                "query": query,
                "session_id": session_id,
                "needs_retrieval": intent_type in ["NEW_SEARCH", "COMPARISON"],
                "confidence": "high"  # Could be enhanced with confidence scoring
            }
            
        except Exception as e:
            logger.error(f"Error recognizing intent: {e}")
            # Default to NEW_SEARCH on error
            return {
                "intent_type": "NEW_SEARCH",
                "query": query,
                "session_id": session_id,
                "needs_retrieval": True,
                "confidence": "low"
            }
    
    def _parse_intent_response(self, response: str) -> str:
        """
        Parse the LLM response to extract intent type.
        """
        response = response.strip().upper()
        
        # Extract intent from response
        if "NEW_SEARCH" in response:
            return "NEW_SEARCH"
        elif "FOLLOW_UP" in response:
            return "FOLLOW_UP"
        elif "CLARIFICATION" in response:
            return "CLARIFICATION"
        elif "COMPARISON" in response:
            return "COMPARISON"
        else:
            # Default to NEW_SEARCH if unclear
            logger.warning(f"Unclear intent response: {response}, defaulting to NEW_SEARCH")
            return "NEW_SEARCH"
    
    def get_system_prompt_for_intent(self, intent_type: str, context: str = "") -> str:
        """
        Get appropriate system prompt based on intent type.
        """
        if intent_type in ["FOLLOW_UP", "CLARIFICATION"]:
            return get_conversation_system_prompt().format(conversation_context=context)
        else:
            return get_enhanced_rag_system_prompt().format(context=context, question="{question}")
    
    def should_retrieve(self, intent_result: Dict[str, Any]) -> bool:
        """
        Determine if retrieval is needed based on intent.
        """
        return intent_result.get("needs_retrieval", True) 