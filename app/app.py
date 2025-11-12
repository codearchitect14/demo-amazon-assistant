import streamlit as st
import asyncio
import time
import re
import logging
import sys
import os
import atexit
from typing import List, Dict

# Configure logging
logger = logging.getLogger(__name__)

# Add current dir & parent to Python path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
for p in (current_dir, parent_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import with fallback
try:
    from api.abstraction import create_api_client, create_api_client_context
    from utils import clear_session_memory
    from shared.utils.error_handling import ErrorHandler
    from shared.utils.validation import DataSanitizer
except ImportError as e:
    logger.error(f"Import error: {e}")
    def create_api_client():
        logger.error("API client not available")
        return None
    def create_api_client_context():
        logger.error("API client context not available")
        return None
    def clear_session_memory(session_id):
        logger.error("Clear session memory not available")
        return True
    class ErrorHandler:
        def handle_error(self, e): return str(e)
    class DataSanitizer:
        def sanitize_string(self, s, max_length=100): return s[:max_length] if s else ""
        def sanitize_url(self, url): return url or ""

# Global API client for session management
_api_client = None

def get_api_client():
    """Get or create API client with proper session management."""
    global _api_client
    if _api_client is None:
        _api_client = create_api_client()
        logger.info("Created global API client", extra={
            "component": "app",
            "operation": "create_api_client"
        })
    return _api_client

def cleanup_api_client():
    """Cleanup API client on application shutdown."""
    global _api_client
    if _api_client is not None:
        try:
            # Run cleanup in event loop if available
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.run_until_complete(_api_client.close())
            logger.info("Cleaned up API client", extra={
                "component": "app",
                "operation": "cleanup_api_client"
            })
        except Exception as e:
            logger.error("Error cleaning up API client", extra={
                "component": "app",
                "operation": "cleanup_api_client",
                "error": str(e)
            })
        finally:
            _api_client = None

# Register cleanup function
atexit.register(cleanup_api_client)

# Initialize utilities
error_handler = ErrorHandler()
sanitizer = DataSanitizer()

# Page config
st.set_page_config(
    page_title="RAG Demo - Enhanced",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject CSS for cards and chat bubbles
st.markdown("""
<style>
/* Light theme background */
.stApp {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  background-attachment: fixed;
  min-height: 100vh;
}

/* Main background override for light theme */
.main {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

/* Ensure the entire page has light background */
body {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

/* Override any dark backgrounds */
[data-testid="stAppViewContainer"] {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

/* Streamlit top bar - override dark background */
[data-testid="stToolbar"] {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
  backdrop-filter: blur(10px);
}

/* Streamlit header/toolbar background */
[data-testid="stHeader"] {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
  backdrop-filter: blur(10px);
}

/* Main menu button and toolbar elements */
[data-testid="stMainMenu"] {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

/* Override any remaining dark backgrounds in Streamlit components */
.stApp > header {
  background: rgba(255, 255, 255, 0.95) !important;
}

.stApp > div[data-testid="stToolbar"] {
  background: rgba(255, 255, 255, 0.95) !important;
}

/* Alternative light gradient options - uncomment to try different schemes */
/*
.stApp {
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
  background-attachment: fixed;
  min-height: 100vh;
}

.stApp {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  background-attachment: fixed;
  min-height: 100vh;
}

.stApp {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  background-attachment: fixed;
  min-height: 100vh;
}
*/

/* Main content area with light glass effect */
.main .block-container {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 20px;
  margin: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* Sidebar with proper contrast and readability */
.sidebar .sidebar-content {
  background: linear-gradient(135deg, rgba(245, 247, 250, 0.95) 0%, rgba(195, 207, 226, 0.95) 100%);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* Title styling for dark text on light background */
h1, h2, h3 {
  color: #2c3e50 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Text color adjustments for better readability on light theme */
p, div {
  color: #2c3e50;
}

/* Chat input styling */
.stTextInput > div > div > input {
  background: rgba(255, 255, 255, 0.95) !important;
  border: 2px solid rgba(52, 73, 94, 0.2) !important;
  backdrop-filter: blur(10px);
  color: #2c3e50 !important;
}

.product-card {
  border: 1px solid rgba(52, 73, 94, 0.2);
  border-radius: 12px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.95);
  text-align: center;
  margin: 8px;
  color: #2c3e50;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  border-color: rgba(52, 73, 94, 0.4);
}

.product-card img {
  width: 100%;
  height: auto;
  border-radius: 4px;
}

.product-card h5 {
  color: #2c3e50;
  margin: 5px 0;
  font-weight: 600;
}

.product-card p {
  color: #34495e;
  margin: 5px 0;
}

/* Dark chat bubbles with different colors for user and AI */
.chat-bubble-user {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  color: #ecf0f1;
  padding: 12px 16px;
  border-radius: 18px;
  margin: 10px 0;
  max-width: fit-content;
  margin-left: auto;
  display: inline-block;
  word-wrap: break-word;
  text-align: right;
  float: right;
  clear: both;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(52, 73, 94, 0.3);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  font-weight: 500;
  position: relative;
}

.chat-bubble-user::after {
  content: "👤";
  position: absolute;
  right: -35px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.chat-bubble-assistant {
  background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%);
  color: #ecf0f1;
  padding: 12px 16px;
  border-radius: 18px;
  margin: 10px 0;
  max-width: fit-content;
  margin-right: auto;
  display: inline-block;
  word-wrap: break-word;
  text-align: left;
  float: left;
  clear: both;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(26, 37, 47, 0.3);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  font-weight: 500;
  position: relative;
}

.chat-bubble-assistant::before {
  content: "🤖";
  position: absolute;
  left: -35px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Enhanced search bar styling */
.stTextInput > div > div > input {
  border-radius: 20px !important;
  border: 2px solid #bdc3c7 !important;
  padding: 8px 16px !important;
  font-size: 14px !important;
  transition: all 0.3s ease !important;
  background: rgba(255, 255, 255, 0.95) !important;
  color: #2c3e50 !important;
}

.stTextInput > div > div > input:focus {
  border-color: #3498db !important;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2) !important;
}

.stTextInput > div > div > input::placeholder {
  color: #7f8c8d !important;
  font-style: italic !important;
}

/* Search results highlight */
.search-highlight {
  background-color: #f39c12;
  color: #2c3e50;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: bold;
}

/* Chat animations */
@keyframes slideInFromRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInFromLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%, 30% { opacity: 1; }
  60% { opacity: 0.4; }
  100% { opacity: 1; }
}

.chat-bubble-user {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  color: #ecf0f1;
  padding: 12px 16px;
  border-radius: 18px;
  margin: 10px 0;
  max-width: fit-content;
  margin-left: auto;
  animation: slideInFromRight 0.5s ease-out;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  display: inline-block;
  word-wrap: break-word;
  text-align: right;
  float: right;
  clear: both;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(52, 73, 94, 0.3);
  font-weight: 500;
  position: relative;
}

.chat-bubble-user:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
  background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
}

.chat-bubble-assistant {
  background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%);
  color: #ecf0f1;
  padding: 12px 16px;
  border-radius: 18px;
  margin: 10px 0;
  max-width: fit-content;
  margin-right: auto;
  animation: slideInFromLeft 0.5s ease-out;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  display: inline-block;
  word-wrap: break-word;
  text-align: left;
  float: left;
  clear: both;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(26, 37, 47, 0.3);
  font-weight: 500;
  position: relative;
}

/* Ensure all text elements within AI assistant m
essages stay light colored */
.chat-bubble-assistant * {
  color: #ecf0f1 !important;
}

.chat-bubble-assistant p {
  color: #ecf0f1 !important;
}

.chat-bubble-assistant span {
  color: #ecf0f1 !important;
}

.chat-bubble-assistant div {
  color: #ecf0f1 !important;
}

.chat-bubble-assistant strong {
  color: #ecf0f1 !important;
}

.chat-bubble-assistant em {
  color: #ecf0f1 !important;
}

.chat-bubble-assistant code {
  color: #ecf0f1 !important;
  background: rgba(255, 255, 255, 0.1) !important;
}

.chat-bubble-assistant a {
  color: #3498db !important;
  text-decoration: underline;
}

.chat-bubble-assistant a:hover {
  color: #5dade2 !important;
}

.chat-bubble-assistant:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
  background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%);
}

.typing-indicator {
  background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
  color: #bdc3c7;
  padding: 10px 14px;
  border-radius: 16px;
  margin: 10px 0;
  max-width: fit-content;
  margin-right: auto;
  animation: typing 2.5s infinite ease-in-out;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  display: inline-block;
  font-style: italic;
  text-align: left;
  float: left;
  clear: both;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(44, 62, 80, 0.3);
  font-weight: 500;
  position: relative;
}

.typing-indicator::before {
  content: "🤖";
  position: absolute;
  left: -35px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.chat-message-new {
  animation: fadeIn 0.6s ease-out;
}

/* Sidebar text improvements for better contrast */
.sidebar h3, .sidebar h4 {
  color: #ffffff !important;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.sidebar p, .sidebar div {
  color: #ffffff;
}

.sidebar .stCaption {
  color: #f8f9fa;
}

/* Button styling for sidebar */
.sidebar .stButton > button {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.sidebar .stButton > button:hover {
  background: linear-gradient(135deg, #2980b9 0%, #3498db 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}

/* Info box styling */
.stAlert {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(52, 73, 94, 0.2);
  border-radius: 8px;
  color: #2c3e50;
}

/* Caption styling */
.stCaption {
  color: #7f8c8d !important;
  font-size: 0.85em;
}

/* Target specific emotion-cache class for transparent background */
.st-emotion-cache-hzygls.e4man113 {
  background: transparent !important;
  color: #2c3e50 !important;
}

</style>
""", unsafe_allow_html=True)

# Session state defaults
st.session_state.setdefault('session_id', f"session_{int(time.time())}")
st.session_state.setdefault('chat_history', [])
st.session_state.setdefault('products', [])

async def stream_chat_response(query, session_id, top_k=5, retrieval_method="title_first"):
    """Stream chat response with proper error handling and logging."""
    start_time = time.time()
    
    logger.info("Starting chat stream", extra={
        "component": "app",
        "operation": "stream_chat_response",
        "session_id": session_id,
        "query_length": len(query),
        "top_k": top_k,
        "retrieval_method": retrieval_method
    })
    
    try:
        api_client = get_api_client()
        if api_client is None:
            logger.error("API client not available for streaming", extra={
                "component": "app",
                "operation": "stream_chat_response",
                "session_id": session_id
            })
            yield {"type": "error", "message": "API client not available"}
            return
            
        chunk_count = 0
        async for chunk in api_client.send_chat_message_stream(
            query=query, session_id=session_id, top_k=top_k, retrieval_method=retrieval_method
        ):
            chunk_count += 1
            yield chunk
            
        processing_time = (time.time() - start_time) * 1000
        logger.info("Chat stream completed", extra={
            "component": "app",
            "operation": "stream_chat_response",
            "session_id": session_id,
            "chunk_count": chunk_count,
            "processing_time_ms": processing_time
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error("Error in chat stream", extra={
            "component": "app",
            "operation": "stream_chat_response",
            "session_id": session_id,
            "error": error_handler.handle_error(e),
            "processing_time_ms": processing_time
        })
        yield {"type": "error", "message": "Failed to get response"}

# Product extraction and cleaning

def clean_product_title(title: str) -> str:
    title = re.sub(r"^Product[:\-]?\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Item[:\-]?\s*", "", title, flags=re.IGNORECASE)
    return sanitizer.sanitize_string(title.rstrip(".,;:!?"), 200)

def clean_product_price(price: str) -> str:
    price = re.sub(r"^(Price|Cost)[:\-]?\s*", "", price, flags=re.IGNORECASE).rstrip(".,;:!?")
    if price.replace(".", "").replace(",", "").isdigit() and not price.startswith("$"):
        price = f"${price}"
    if price.startswith("$"):
        try:
            num = price[1:].replace(",", "")
            if "." in num:
                i, d = num.split(".")
                price = f"${int(i):,}.{d}"
            else:
                price = f"${int(num):,}"
        except:
            pass
    return price

from typing import Dict

def extract_products_from_context(context: str) -> List[Dict]:
    products = []
    for section in context.split("\n\n"):
        if "Title:" in section or "Price:" in section:
            prod = {}
            m = re.search(r"Title[:\s]+([^\n]+)", section, re.IGNORECASE)
            if m: prod["title"] = clean_product_title(m.group(1).strip())
            m = re.search(r"Price[:\s]+([^\n]+)", section, re.IGNORECASE)
            if m: prod["price"] = clean_product_price(m.group(1).strip())
            m = re.search(r"https?://[^\s<>\"]+\.(?:jpg|jpeg|png|gif|webp)", section)
            if m: prod["image"] = sanitizer.sanitize_url(m.group(0))
            if prod: products.append(prod)
    return products

# Sidebar layout with proper cards
def create_reactive_sidebar():
    with st.sidebar:
        st.markdown("<h3>🛍️ Product Gallery</h3>", unsafe_allow_html=True)
        # st.markdown("---")
        
        # Beautiful search bar
        st.markdown("<h4>🔍 Search Products</h4>", unsafe_allow_html=True)
        
        # Search input with clear button
        col1, col2 = st.columns([4, 1])
        with col1:
            search_query = st.text_input(
                "Search products...",
                placeholder="Type to search products...",
                key="product_search",
                help="Search through extracted products by title or price",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("🗑️", help="Clear search", key="clear_search"):
                st.session_state.product_search = ""
                st.rerun()
        
        # Show search status
        if search_query:
            st.caption(f"🔍 Searching for: '{search_query}'")
        
        # Filter products based on search
        filtered_products = st.session_state.products
        if search_query:
            search_lower = search_query.lower()
            filtered_products = [
                p for p in st.session_state.products
                if (search_lower in p.get('title', '').lower() or 
                    search_lower in p.get('price', '').lower())
            ]
            
            # Highlight search terms in results
            for product in filtered_products:
                if 'title' in product:
                    title = product['title']
                    if search_lower in title.lower():
                        # Simple highlighting - could be enhanced with regex
                        product['title_highlighted'] = title
                if 'price' in product:
                    price = product['price']
                    if search_lower in price.lower():
                        product['price_highlighted'] = price
        
        # st.markdown("---")
        # st.markdown("<h4>🤖 System Status</h4>", unsafe_allow_html=True)
        # info = (
        #     f"**Session ID:** `{st.session_state.session_id[:20]}...`\n\n"
        #     f"**Conversation:** {'Active' if st.session_state.chat_history else 'New'}\n\n"
        #     f"**Products Found:** {len(filtered_products)}"
        # )
        # st.info(info)

        if filtered_products:
            st.markdown("---")
            st.markdown(f"<h4>📦 Products ({len(filtered_products)})</h4>", unsafe_allow_html=True)
            prods = filtered_products[-10:]  # Show last 10 filtered products
            for i in range(0, len(prods), 2):
                cols = st.columns(2)
                for idx, col in enumerate(cols):
                    if i+idx < len(prods):
                        p = prods[i+idx]
                        col.markdown(
                            f"<div class='product-card'>"
                            f"<img src='{p.get('image','https://via.placeholder.com/150')}' alt='prod' />"
                            f"<h5>{p.get('title','Unknown')}</h5>"
                            f"<p>{p.get('price','N/A')}</p>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
        st.markdown("---")
        # c1, c2 = st.columns(2)
        # with c1:
        #     if st.button("🗑️ Clear Memory"):
        #         asyncio.run(clear_session_memory(st.session_state.session_id))
        #         st.session_state.chat_history.clear()
        #         st.rerun()
        # with c2:
        #     if st.button("🔄 New Session"):
        #         st.session_state.session_id = f"session_{int(time.time())}"
        #         st.session_state.chat_history.clear()
        #         st.session_state.products.clear()
        #         st.rerun()

# Main app
def main():
    st.title("🤖 Enhanced RAG Demo")
    st.markdown("**Intelligent Product Search & Recommendation System**")
    create_reactive_sidebar()
    st.markdown("---")
    # st.markdown("### 💬 Chat with AI Assistant")

    # Render chat history with animations
    if st.session_state.chat_history:
        for i, msg in enumerate(st.session_state.chat_history):
            cls = 'chat-bubble-user' if msg['role']=='user' else 'chat-bubble-assistant'
            # Add animation delay for staggered effect
            animation_delay = f"animation-delay: {i * 0.1}s;"
            st.markdown(
                f"<div class='{cls}' style='{animation_delay}'>{msg['content']}</div>", 
                unsafe_allow_html=True
            )

    # Capture user input with animation
    if prompt := st.chat_input("Ask me about products..."):
        # Add user message with animation
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()

    # Generate assistant reply
    if st.session_state.chat_history and st.session_state.chat_history[-1]['role']=='user':
        user_msg = st.session_state.chat_history[-1]['content']
        placeholder = st.empty()
        placeholder.markdown(
            "<div class='typing-indicator'>🤖 AI is thinking...</div>", 
            unsafe_allow_html=True
        )

        async def get_response():
            full, raw = "", {"context":"","metadata":{}}
            async for chunk in stream_chat_response(user_msg, st.session_state.session_id):
                if chunk.get("type") == "token":
                    full += chunk.get("content","")
                    # Enhanced typing animation with cursor
                    cursor_animation = "animation: typing 2s infinite;"
                    placeholder.markdown(
                        f"<div class='chat-bubble-assistant' style='{cursor_animation}'>"
                        f"{full}<span style='display: inline-block; width: 2px; height: 1em; background: #333; margin-left: 2px; animation: typing 2s infinite;'></span>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
                elif chunk.get("type") == "complete":
                    # Final message without cursor
                    placeholder.markdown(
                        f"<div class='chat-bubble-assistant chat-message-new'>{full}</div>", 
                        unsafe_allow_html=True
                    )
                    raw = chunk
                    break
                else:
                    placeholder.markdown(
                        "<div class='chat-bubble-assistant'>❌ Error from API</div>", 
                        unsafe_allow_html=True
                    )
                    break
            return full, raw

        # Use asyncio.run() carefully in Streamlit context
        try:
            full_resp, raw_data = asyncio.run(get_response())
        except RuntimeError:
            # If there's already a running event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                full_resp, raw_data = loop.run_until_complete(get_response())
            finally:
                loop.close()
        # Add assistant response with animation trigger
        st.session_state.chat_history.append({"role":"assistant","content":full_resp})
        
        # Extract products
        ctx = raw_data.get("context", "")
        if ctx:
            new_ps = extract_products_from_context(ctx)
            if new_ps:
                st.session_state.products.extend(new_ps)
                st.session_state.products = st.session_state.products[-10:]
        
        # Trigger rerun to show new message with animation
        st.rerun()

if __name__ == "__main__":
    main()
