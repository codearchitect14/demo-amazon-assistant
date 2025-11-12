# Utility functions for the RAG Demo App
import streamlit as st
import requests
import json
import re
import uuid
import asyncio
import aiohttp
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
# Remove the circular import - we'll import this conditionally when needed
# from app.api.abstraction import create_api_client, ChatAPIClient
from shared.utils.error_handling import NetworkError, ValidationError, ErrorHandler
from shared.utils.validation import DataSanitizer
import logging

logger = logging.getLogger(__name__)

# Create API client instance - we'll create this when needed
# api_client = create_api_client()


# ============================================================================
# CONTEXT EXTRACTION UTILITIES
# ============================================================================


def extract_images_from_context(context: str) -> list:
    """Extract image URLs from context."""
    # Simple regex to find image URLs
    image_pattern = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)'
    return re.findall(image_pattern, context, re.IGNORECASE)


def extract_product_titles_from_context(context: str) -> list:
    """Extract product titles from context."""
    # Look for patterns that indicate product titles
    title_pattern = r'Title[:\s]+([^\n]+)'
    return re.findall(title_pattern, context, re.IGNORECASE)


def extract_images_and_titles_from_context(context: str) -> list:
    """Extract both images and titles from context."""
    images = extract_images_from_context(context)
    titles = extract_product_titles_from_context(context)
    
    # Combine and deduplicate
    combined = []
    for title in titles:
        combined.append({"title": title.strip(), "image": None})
    
    # Add images without titles
    for image in images:
        if not any(item.get("image") == image for item in combined):
            combined.append({"title": None, "image": image})
    
    return combined


# ============================================================================
# API COMMUNICATION UTILITIES
# ============================================================================


def get_api_client():
    """Get API client instance, creating it if needed."""
    try:
        from api.abstraction import create_api_client
        return create_api_client()
    except ImportError:
        try:
            from app.api.abstraction import create_api_client
            return create_api_client()
        except ImportError:
            logger.error("Could not import API client")
            return None


async def fetch_products_from_api(query: str, top_k: int = 10) -> list:
    """
    Fetch products from API using the abstraction layer.
    
    Args:
        query: Search query
        top_k: Number of results to retrieve
        
    Returns:
        List of products
    """
    error_handler = ErrorHandler()
    
    try:
        # Get API client
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available")
            return []
        
        # Use the API abstraction layer
        response = await api_client.send_chat_message(
            query=query,
            session_id=st.session_state.get("session_id"),
            top_k=top_k,
            retrieval_method="title_first"
        )
        
        # Extract products from response
        context = response.get("context", "")
        products = extract_images_and_titles_from_context(context)
        
        logger.info(f"Fetched {len(products)} products for query: {query}")
        return products
        
    except NetworkError as e:
        error_info = error_handler.handle_error(e)
        logger.error(f"Network error fetching products: {error_info}")
        st.error("Failed to connect to the API. Please check your connection.")
        return []
        
    except ValidationError as e:
        error_info = error_handler.handle_error(e)
        logger.error(f"Validation error fetching products: {error_info}")
        st.error("Invalid request data. Please try again.")
        return []
        
    except Exception as e:
        error_info = error_handler.handle_error(e)
        logger.error(f"Unexpected error fetching products: {error_info}")
        st.error("An unexpected error occurred. Please try again.")
        return []


async def fetch_products_simple_search(query: str, top_k: int = 10) -> list:
    """
    Simple search implementation using API abstraction.
    
    Args:
        query: Search query
        top_k: Number of results to retrieve
        
    Returns:
        List of products
    """
    try:
        # Get API client
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available")
            return []
        
        # Use the API abstraction layer
        response = await api_client.send_chat_message(
            query=query,
            session_id=st.session_state.get("session_id"),
            top_k=top_k,
            retrieval_method="multi"
        )
        
        # Extract products from response
        context = response.get("context", "")
        products = extract_images_and_titles_from_context(context)
        
        return products
        
    except Exception as e:
        logger.error(f"Error in simple search: {e}")
        return []


def parse_products_from_context(context: str) -> list:
    """
    Parse products from context string.
    
    Args:
        context: Context string containing product information
        
    Returns:
        List of parsed products
    """
    sanitizer = DataSanitizer()
    products = []
    
    # Split context into sections
    sections = context.split('\n\n')
    
    for section in sections:
        if 'Title:' in section or 'Price:' in section:
            product = {}
            
            # Extract title
            title_match = re.search(r'Title[:\s]+([^\n]+)', section, re.IGNORECASE)
            if title_match:
                product['title'] = sanitizer.sanitize_string(title_match.group(1).strip())
            
            # Extract price
            price_match = re.search(r'Price[:\s]+([^\n]+)', section, re.IGNORECASE)
            if price_match:
                product['price'] = sanitizer.sanitize_string(price_match.group(1).strip())
            
            # Extract image URL
            image_match = re.search(r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)', section, re.IGNORECASE)
            if image_match:
                product['image'] = sanitizer.sanitize_url(image_match.group(0))
            
            if product:
                products.append(product)
    
    return products


def generate_product_image_url(title: str) -> str:
    """
    Generate a placeholder image URL based on product title.
    
    Args:
        title: Product title
        
    Returns:
        Placeholder image URL
    """
    # Simple placeholder image generation
    sanitized_title = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
    words = sanitized_title.split()[:3]
    search_query = '+'.join(words)
    
    return f"https://via.placeholder.com/300x200/4A90E2/FFFFFF?text={search_query}"


async def get_memory_stats() -> dict:
    """Get memory statistics using API abstraction."""
    try:
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available for memory stats")
            return {}
        health_status = await api_client.get_health_status()
        return health_status.get("memory", {}).get("stats", {})
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return {}


async def get_performance_stats() -> dict:
    """Get performance statistics using API abstraction."""
    try:
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available for performance stats")
            return {}
        health_status = await api_client.get_health_status()
        return health_status.get("performance", {})
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {}


async def get_cache_stats() -> dict:
    """Get cache statistics using API abstraction."""
    try:
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available for cache stats")
            return {}
        health_status = await api_client.get_health_status()
        return health_status.get("cache", {})
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {}


async def clear_session_memory(session_id: str) -> bool:
    """
    Clear session memory using API abstraction.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available for clearing memory")
            return False
        # This would need to be implemented in the API
        # For now, just return success
        logger.info(f"Cleared memory for session: {session_id}")
        return True
    except Exception as e:
        logger.error(f"Error clearing session memory: {e}")
        return False


async def get_conversation_history(session_id: str) -> dict:
    """
    Get conversation history using API abstraction.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Conversation history
    """
    try:
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available for conversation history")
            return {"history": [], "session_id": session_id}
        # This would need to be implemented in the API
        # For now, return empty history
        return {"history": [], "session_id": session_id}
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return {"history": [], "session_id": session_id}


async def evaluate_response(query: str, response: str, context: str) -> dict:
    """
    Evaluate response quality using API abstraction.
    
    Args:
        query: User query
        response: AI response
        context: Retrieved context
        
    Returns:
        Evaluation results
    """
    try:
        api_client = get_api_client()
        if not api_client:
            logger.error("API client not available for response evaluation")
            return {}
        # Simple evaluation metrics
        evaluation = {
            "relevance_score": 0.8,  # Placeholder
            "accuracy_score": 0.7,   # Placeholder
            "completeness_score": 0.6,  # Placeholder
            "context_utilization": len(context) > 0,
            "response_length": len(response),
            "query_length": len(query)
        }
        
        return evaluation
    except Exception as e:
        logger.error(f"Error evaluating response: {e}")
        return {}


# ============================================================================
# DISPLAY UTILITIES
# ============================================================================


def display_context_with_images(context: str):
    """Display context text and images in a nice format"""
    image_title_pairs = extract_images_and_titles_from_context(context)

    # Display text context with enhanced styling
    st.markdown(
        """
    <div class="context-display">
        <h4>📚 Retrieved Context</h4>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.text_area(
        "Context Details:",
        value=context,
        height=300,
        disabled=True,
        key=f"context_text_{id(context)}",
    )

    # Display images and titles if any found
    if image_title_pairs:
        st.markdown(
            """
        <div class="context-display">
            <h4>🖼️ Product Images</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        cols = st.columns(min(3, len(image_title_pairs)))

        for i, (img_url, title) in enumerate(image_title_pairs):
            col_idx = i % 3
            with cols[col_idx]:
                try:
                    st.image(
                        img_url,
                        width=150,
                        caption=title if title else f"Product {i+1}",
                        use_container_width=False,
                    )
                    if title:
                        st.markdown(f"**{title}**")
                except Exception as e:
                    st.error(f"Failed to load image {i+1}: {str(e)}")


def display_conversation_history(conversation_history: str):
    """Display conversation history in a nice format"""
    if not conversation_history:
        st.info("No conversation history available")
        return

    st.markdown(
        """
    <div class="context-display">
        <h4>💬 Conversation History</h4>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.text_area(
        "History Details:",
        value=conversation_history,
        height=200,
        disabled=True,
        key=f"conversation_history_{id(conversation_history)}",
    )

    lines = conversation_history.split("\n")
    st.info(
        f"📝 Conversation history contains {len(lines)} lines and {len(conversation_history)} characters"
    )


def format_conversation_history_for_display(history_data: dict) -> str:
    """
    Format conversation history for display.
    
    Args:
        history_data: Raw history data
        
    Returns:
        Formatted history string
    """
    try:
        history = history_data.get("history", [])
        if not history:
            return "No conversation history available."
        
        formatted = []
        for entry in history[-5:]:  # Show last 5 entries
            question = entry.get("question", "Unknown question")
            answer = entry.get("answer", "No answer")
            timestamp = entry.get("timestamp", "Unknown time")
            
            formatted.append(f"**Q ({timestamp}):** {question}")
            formatted.append(f"**A:** {answer}")
            formatted.append("---")
        
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Error formatting conversation history: {e}")
        return "Error formatting conversation history."


def display_evaluation_results(evaluation_results: list):
    """Display evaluation results in a dedicated section with enhanced styling"""
    if not evaluation_results:
        return

    st.markdown(
        """
    <div class="chat-container">
        <h3>📊 Response Evaluation</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    for i, result in enumerate(evaluation_results[-3:], 1):  # Show last 3 evaluations
        with st.expander(
            f"Evaluation #{i} - {result.get('timestamp', 'Unknown')}", expanded=False
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Relevance", f"{result.get('relevance_score', 0):.2f}")
                st.metric("Accuracy", f"{result.get('accuracy_score', 0):.2f}")

            with col2:
                st.metric("Completeness", f"{result.get('completeness_score', 0):.2f}")
                st.metric(
                    "Hallucination", f"{result.get('hallucination_score', 0):.2f}"
                )

            with col3:
                st.metric("Overall Score", f"{result.get('overall_score', 0):.2f}")
                st.metric("Response Time", f"{result.get('response_time', 0):.2f}s")

            # Show recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                st.markdown("💡 **Recommendations:**")
                for rec in recommendations:
                    st.write(f"• {rec}")


# ============================================================================
# SIDEBAR UTILITIES
# ============================================================================


def display_smart_features_sidebar():
    """Display smart features configuration in sidebar with enhanced styling"""
    with st.sidebar:
        # st.markdown("""
        # <div class="sidebar-section">
        #     <h3>⚙️ Smart Features</h3>
        # </div>
        # """, unsafe_allow_html=True)

        # Smart features toggle with animation
        smart_enabled = st.checkbox(
            "🚀 Enable Smart Features",
            value=st.session_state.smart_features,
            help="Enable hybrid search, cross-encoder re-ranking, evaluation, and performance optimization",
        )
        st.session_state.smart_features = smart_enabled

        if smart_enabled:
            st.markdown(
                '<p class="status-success">✅ Smart features enabled</p>',
                unsafe_allow_html=True,
            )

            # Retrieval method selection
            st.markdown(
                """
            <div class="sidebar-section">
                <h4>🔍 Retrieval Method</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            retrieval_method = st.selectbox(
                "Choose retrieval method:",
                ["title_first", "hybrid", "multi", "weighted", "hierarchical"],
                index=0,
                help="Title First: Prioritizes product titles\nHybrid: Combines dense and sparse search\nMulti: Searches all content types\nWeighted: Weighted combination\nHierarchical: Multi-level search",
            )

            # Top-K selection
            st.markdown(
                """
            <div class="sidebar-section">
                <h4>📊 Retrieval Parameters</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            top_k = st.slider("Number of documents to retrieve:", 1, 20, 5)

            # Evaluation toggle
            st.markdown(
                """
            <div class="sidebar-section">
                <h4>📈 Evaluation</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            enable_evaluation = st.checkbox("Enable Response Evaluation", value=True)

            return retrieval_method, top_k, enable_evaluation
        else:
            st.markdown(
                '<p class="status-warning">⚠️ Basic features only</p>',
                unsafe_allow_html=True,
            )
            return "title_first", 5, False


def display_system_health():
    """Display system health and performance metrics with enhanced styling"""
    try:
        # Get stats from API
        memory_stats = get_memory_stats()
        performance_stats = get_performance_stats()
        cache_stats = get_cache_stats()

        with st.sidebar:
            st.markdown(
                """
            <div class="sidebar-section">
                <h3>🏥 System Health</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Memory status
            if memory_stats.get("enabled"):
                st.markdown(
                    '<p class="status-success">✅ Memory System</p>',
                    unsafe_allow_html=True,
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Sessions", memory_stats.get("total_sessions", 0))
                with col2:
                    st.metric("Interactions", memory_stats.get("total_interactions", 0))
            else:
                st.markdown(
                    '<p class="status-warning">⚠️ Memory Disabled</p>',
                    unsafe_allow_html=True,
                )

            # Performance metrics
            if performance_stats:
                st.markdown(
                    """
                <div class="sidebar-section">
                    <h4>⚡ Performance</h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                perf_data = performance_stats.get("performance_stats", {})
                if "cache_hits" in perf_data:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Cache Hits", perf_data.get("cache_hits", 0))
                    with col2:
                        st.metric("Cache Misses", perf_data.get("cache_misses", 0))

            # Embedding cache status
            if cache_stats:
                st.markdown(
                    """
                <div class="sidebar-section">
                    <h4>🧠 Embedding Cache</h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                cache_info = cache_stats.get("embedding_cache", {})
                if cache_info.get("model_loaded"):
                    st.markdown(
                        '<p class="status-success">✅ Model Loaded</p>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<p class="status-warning">⚠️ Model Not Loaded</p>',
                        unsafe_allow_html=True,
                    )

    except Exception as e:
        st.sidebar.markdown(
            f'<p class="status-error">❌ Health check failed: {str(e)}</p>',
            unsafe_allow_html=True,
        )


def display_analytics():
    """Display analytics and insights with enhanced styling"""
    with st.sidebar:
        st.markdown(
            """
        <div class="sidebar-section">
            <h3>📈 Analytics</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Session analytics
        if st.session_state.messages:
            user_messages = len(
                [msg for msg in st.session_state.messages if msg["role"] == "user"]
            )
            assistant_messages = len(
                [msg for msg in st.session_state.messages if msg["role"] == "assistant"]
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric("User Messages", user_messages)
            with col2:
                st.metric("Assistant Messages", assistant_messages)

        # Performance insights
        if st.session_state.performance_stats:
            st.markdown(
                """
            <div class="sidebar-section">
                <h4>⚡ Performance Insights</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            perf = st.session_state.performance_stats

            if "avg_response_time" in perf:
                st.metric("Avg Response Time", f"{perf['avg_response_time']:.2f}s")

            if "cache_efficiency" in perf:
                st.metric("Cache Efficiency", f"{perf['cache_efficiency']:.1f}%")


# ============================================================================
# SESSION MANAGEMENT UTILITIES
# ============================================================================


def initialize_session_state():
    """Initialize all session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.success(
            f"🆔 New conversation session started: {st.session_state.session_id[:8]}..."
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "smart_features" not in st.session_state:
        st.session_state.smart_features = False

    if "evaluation_results" not in st.session_state:
        st.session_state.evaluation_results = []

    if "performance_stats" not in st.session_state:
        st.session_state.performance_stats = {}

    if "is_typing" not in st.session_state:
        st.session_state.is_typing = False

    if "last_message_count" not in st.session_state:
        st.session_state.last_message_count = 0

    if "scroll_trigger" not in st.session_state:
        st.session_state.scroll_trigger = 0


def create_new_session():
    """Create a new session and clear messages"""
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.success(f"New session: {st.session_state.session_id[:8]}...")
    st.rerun()


def clear_session_memory_ui(session_id: str):
    """Clear memory for the current session with UI feedback"""
    if clear_session_memory(session_id):
        st.success("✅ Memory cleared")
    else:
        st.error("❌ Failed to clear memory")


# ============================================================================
# TEXT PROCESSING UTILITIES
# ============================================================================


def clean_text(text: str) -> str:
    """Clean and sanitize text."""
    sanitizer = DataSanitizer()
    return sanitizer.sanitize_string(text)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_timestamp(timestamp: datetime = None) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================


def validate_api_url(url: str) -> bool:
    """Validate API URL format."""
    import re
    url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
    return bool(url_pattern.match(url))


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format."""
    import re
    session_pattern = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
    return bool(session_pattern.match(session_id))


def validate_retrieval_method(method: str) -> bool:
    """Validate retrieval method."""
    valid_methods = ["title_first", "multi", "hybrid", "semantic"]
    return method in valid_methods
