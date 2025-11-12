"""
Centralized prompts for the Amazon RAG Demo application.

This module contains all the prompts used throughout the application to ensure
consistency and easy maintenance.
"""

# =============================================================================
# RAG SYSTEM PROMPTS
# =============================================================================

RAG_SYSTEM_PROMPT = """You are a helpful AI assistant specializing in product information and recommendations. Your role is to:

1. Answer user questions accurately based on the provided context about products
2. Provide detailed product information from whatever fields are available (prices, ratings, features, etc.)
3. Make helpful comparisons between products when relevant
4. Recommend products based on user needs and preferences

Guidelines:
- Always base your answers on the provided context
- The product data structure may vary - work with whatever fields are available
- If the context doesn't contain enough information, clearly state this
- Provide specific details when available (product URLs, prices, ratings, features, etc.)
- Prefer using direct product URLs instead of internal IDs like ASIN or product_id
- Provide Product URL with every product
- Format your response in a clear, readable manner
- Use conversation history to provide more contextual and personalized responses"""

CONVERSATION_ONLY_SYSTEM_PROMPT = """You are a helpful AI assistant specializing in product information and recommendations. Your role is to:

1. Answer user questions based on the conversation history and your knowledge
2. Provide detailed information about products discussed in the conversation
3. Make helpful comparisons between products when relevant
4. Recommend products based on user needs and preferences

Guidelines:
- Base your answers on the conversation history and your knowledge
- If the conversation history contains relevant product information, use it
- If the user is asking about products not in the conversation history, suggest they ask a new question to search for products
- Provide specific details when available from conversation history
- Format your response in a clear, readable manner
- Be conversational and contextual based on the ongoing discussion
- If you need to search for new products, suggest the user ask a new question"""

# =============================================================================
# RAG USER PROMPT TEMPLATES
# =============================================================================

RAG_USER_PROMPT_TEMPLATE = """{conversation_history_section}PRODUCT CONTEXT:
{context}

QUESTION: {question}

Please provide a comprehensive answer based on the context above. If the context doesn't contain sufficient information to fully answer the question, please indicate what information is missing. If product URLs are available in the context, include them in your answer."""

# =============================================================================
# CONVERSATION HISTORY TEMPLATES
# =============================================================================

RAG_CONVERSATION_HISTORY_TEMPLATE = """CONVERSATION HISTORY:
{conversation_history}

"""

# =============================================================================
# PROMPT BUILDING FUNCTIONS
# =============================================================================


def build_rag_user_prompt(
    context: str, question: str, conversation_history: str = ""
) -> str:
    """
    Build a user prompt for RAG responses with optional conversation history.

    Args:
        context: The retrieved product context
        question: The user's question
        conversation_history: Optional conversation history

    Returns:
        Formatted user prompt string for RAG responses
    """
    import logging

    logger = logging.getLogger(__name__)

    conversation_history_section = ""
    if conversation_history:
        conversation_history_section = RAG_CONVERSATION_HISTORY_TEMPLATE.format(
            conversation_history=conversation_history
        )
        logger.info(
            f"Building prompt with conversation history: {len(conversation_history)} characters"
        )
        logger.debug(f"Conversation history: {conversation_history[:200]}...")
    else:
        logger.info("Building prompt without conversation history")

    prompt = RAG_USER_PROMPT_TEMPLATE.format(
        conversation_history_section=conversation_history_section,
        context=context,
        question=question,
    )

    logger.info(f"Built prompt with {len(prompt)} total characters")
    return prompt


def get_rag_system_prompt() -> str:
    """
    Get the system prompt for RAG-based AI assistant responses.

    Returns:
        System prompt string for RAG responses
    """
    return RAG_SYSTEM_PROMPT


async def should_retrieve_new_data_llm_async(
    question: str, conversation_history: str = ""
) -> bool:
    """
    Use LLM to determine if new data retrieval is needed (async version).
    This is more intelligent than keyword-based detection.

    Args:
        question: The user's question
        conversation_history: The conversation history

    Returns:
        True if new data should be retrieved, False if conversation history is sufficient
    """
    import logging

    logger = logging.getLogger(__name__)

    # If no conversation history, always retrieve
    if not conversation_history:
        logger.info("No conversation history available - retrieving new data")
        return True

    # Create a decision prompt for the LLM
    decision_prompt = f"""You are an AI assistant that determines whether a user's question requires new information retrieval or can be answered using existing conversation history.

CONVERSATION HISTORY:
{conversation_history}

CURRENT QUESTION: {question}

TASK: Determine if this question requires NEW DATA RETRIEVAL or can be answered using the CONVERSATION HISTORY.

RULES:
- If the question asks about products/information NOT mentioned in the conversation history → RETRIEVE NEW DATA
- If the question asks about products/information ALREADY mentioned in the conversation history → USE CONVERSATION HISTORY
- If the question is a follow-up about previously discussed items → USE CONVERSATION HISTORY
- If the question asks for new products or different categories → RETRIEVE NEW DATA
- If the question uses words like "those", "them", "the ones", "compare", "which of those" → USE CONVERSATION HISTORY
- If the question uses words like "find", "search", "show me", "get", "new", "different" → RETRIEVE NEW DATA

RESPONSE FORMAT:
Answer with exactly one word: either "RETRIEVE" or "CONVERSATION"

Your decision:"""

    try:
        from rag.rag_utils import llm_client

        # Use the LLM to make the decision
        messages = [
            {
                "role": "system",
                "content": "You are a decision-making assistant. Respond with exactly one word: RETRIEVE or CONVERSATION.",
            },
            {"role": "user", "content": decision_prompt},
        ]

        # Use the fallback model for this decision (it's faster and cheaper)
        response = await llm_client.generate_response_async(messages)
        decision = response.strip().upper()

        logger.info(f"LLM decision for question '{question}': {decision}")

        if decision == "RETRIEVE":
            logger.info("LLM decided to retrieve new data")
            return True
        elif decision == "CONVERSATION":
            logger.info("LLM decided to use conversation history")
            return False
        else:
            # Fallback to keyword-based detection if LLM response is unclear
            logger.warning(
                f"Unclear LLM response: '{decision}', falling back to keyword detection"
            )
            return should_retrieve_new_data_keywords(question, conversation_history)

    except Exception as e:
        logger.error(
            f"Error in LLM-based decision: {e}, falling back to keyword detection"
        )
        return should_retrieve_new_data_keywords(question, conversation_history)


def should_retrieve_new_data_keywords(
    question: str, conversation_history: str = ""
) -> bool:
    """
    Fallback keyword-based detection for when LLM decision fails.
    """
    import logging

    logger = logging.getLogger(__name__)

    # If no conversation history, always retrieve
    if not conversation_history:
        logger.info("No conversation history available - retrieving new data")
        return True

    # Keywords that suggest the user wants new information
    new_info_keywords = [
        "search",
        "find",
        "look for",
        "show me",
        "get",
        "retrieve",
        "what are",
        "which",
        "recommend",
        "suggest",
        "new",
        "different",
        "other",
        "more",
        "additional",
        "latest",
        "best",
        "top",
    ]

    # Keywords that suggest the user is asking about existing conversation
    conversation_keywords = [
        "what did you say",
        "what was",
        "you mentioned",
        "you said",
        "from before",
        "earlier",
        "previously",
        "that",
        "those",
        "the ones",
        "the products",
        "them",
        "it",
        "this",
        "compare",
        "thse",
        "these",
        "they",
        "their",
    ]

    question_lower = question.lower()

    # Check for new information keywords
    has_new_info_keywords = any(
        keyword in question_lower for keyword in new_info_keywords
    )

    # Check for conversation keywords
    has_conversation_keywords = any(
        keyword in question_lower for keyword in conversation_keywords
    )

    # Debug logging
    logger.info(f"Question: '{question}'")
    logger.info(f"Has new info keywords: {has_new_info_keywords}")
    logger.info(f"Has conversation keywords: {has_conversation_keywords}")

    # If user explicitly asks for new information, retrieve
    if has_new_info_keywords and not has_conversation_keywords:
        logger.info("Question contains new information keywords - retrieving new data")
        return True

    # If user asks about conversation, don't retrieve
    if has_conversation_keywords:
        logger.info("Question references conversation history - using existing data")
        return False

    # Default: if we have conversation history, try to use it first
    logger.info("Using conversation history for contextual response")
    return False


# Use LLM-based detection by default
def should_retrieve_new_data(question: str, conversation_history: str = "") -> bool:
    """
    Determine if new data retrieval is needed using LLM-based decision making.

    Args:
        question: The user's question
        conversation_history: The conversation history

    Returns:
        True if new data should be retrieved, False if conversation history is sufficient
    """
    return should_retrieve_new_data_llm(question, conversation_history)


def build_conversation_only_prompt(question: str, conversation_history: str) -> str:
    """
    Build a prompt for conversation-only responses (no new data retrieval).

    Args:
        question: The user's question
        conversation_history: The conversation history

    Returns:
        Formatted prompt string for conversation-only responses
    """
    import logging

    logger = logging.getLogger(__name__)

    prompt = f"""CONVERSATION HISTORY:
{conversation_history}

CURRENT QUESTION: {question}

Please answer the question based on the conversation history above. If the conversation history contains relevant information, use it to provide a detailed response. If the question cannot be answered from the conversation history, suggest that the user ask a new question to search for products."""

    logger.info(f"Built conversation-only prompt with {len(prompt)} characters")
    return prompt


def get_conversation_only_system_prompt() -> str:
    """
    Get the system prompt for conversation-only responses (no new data retrieval).

    Returns:
        System prompt string for conversation-only responses
    """
    return CONVERSATION_ONLY_SYSTEM_PROMPT


def get_intent_recognition_system_prompt() -> str:
    """
    System prompt for intent recognition to decide whether to retrieve new data or use conversation context.
    """
    return """You are an intent recognition system for a product search and recommendation platform.

Your job is to analyze user queries and determine the appropriate action:

1. **NEW_SEARCH**: User wants to search for new products or start a new topic
   - Examples: "show me laptops", "find gaming computers", "search for bags"
   - Keywords: "show", "find", "search", "look for", "get", "recommend"

2. **FOLLOW_UP**: User is asking follow-up questions about previously discussed products
   - Examples: "tell me more about that laptop", "what about the price?", "is it good for gaming?"
   - Keywords: "that", "this", "it", "the", "more", "tell me", "what about"

3. **CLARIFICATION**: User needs clarification about current context
   - Examples: "which one?", "what do you mean?", "can you explain?"
   - Keywords: "which", "what do you mean", "explain", "clarify"

4. **COMPARISON**: User wants to compare products
   - Examples: "compare these laptops", "which is better?", "what's the difference?"
   - Keywords: "compare", "better", "difference", "versus", "vs"

Respond with ONLY the intent type: NEW_SEARCH, FOLLOW_UP, CLARIFICATION, or COMPARISON.

Consider the conversation history when making your decision. If the user refers to previously mentioned products, use FOLLOW_UP."""


def get_conversation_system_prompt() -> str:
    """
    System prompt for follow-up conversations without new retrieval.
    """
    return """You are a helpful product assistant with access to previously retrieved product information.

You have detailed information about products that were discussed earlier in the conversation. Use this information to answer follow-up questions.

**Guidelines:**
- Answer based on the product information you have
- Be specific about product details, prices, features
- If asked about something not in your context, politely mention you don't have that information
- Be conversational and helpful
- Don't make up information you don't have

**Available Product Information:**
{conversation_context}

Remember: You're continuing a conversation about specific products. Use the information you have to provide helpful, accurate responses."""


def get_enhanced_rag_system_prompt() -> str:
    """
    Enhanced system prompt for when new retrieval is needed.
    """
    return """You are an intelligent product search and recommendation assistant. You help users find and understand products based on their needs.

**Your Capabilities:**
- Search and retrieve relevant product information
- Provide detailed product analysis and recommendations
- Answer questions about product features, prices, and specifications
- Compare products and highlight differences
- Give personalized recommendations based on user needs

**Guidelines:**
- Use the retrieved product information to provide accurate, helpful responses
- Be specific about product details, prices, features, and reviews
- If a product seems relevant to the user's needs, recommend it with reasoning
- Mention key features, pros/cons, and user reviews when available
- Be conversational and engaging
- Don't make up information not present in the retrieved data

**Retrieved Product Information:**
{context}

**User Query:** {question}

Provide a helpful, informative response based on the product information above."""


# =============================================================================
# LEGACY FUNCTION NAMES (for backward compatibility)
# =============================================================================


def build_user_prompt(
    context: str, question: str, conversation_history: str = ""
) -> str:
    """
    Legacy function name for backward compatibility.
    Use build_rag_user_prompt() for new code.
    """
    return build_rag_user_prompt(context, question, conversation_history)


def get_system_prompt() -> str:
    """
    Legacy function name for backward compatibility.
    Use get_rag_system_prompt() for new code.
    """
    return get_rag_system_prompt()
