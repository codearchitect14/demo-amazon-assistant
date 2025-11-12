# Clean Dark Theme CSS for User-Friendly Interface


def get_css_styles():
    """Return clean, minimal dark theme CSS styles"""
    return """
<style>
    /* Clean dark theme */
    .stApp {
        background: #0f0f23;
        color: #ffffff;
    }
    
    /* Simple header */
    .simple-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .simple-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    
    .simple-header p {
        font-size: 1.1rem;
        color: #b0b0b0;
        margin: 0;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid #2a2a3e;
    }
    
    .sidebar-header h3 {
        color: #ffffff;
        margin: 0;
        font-size: 1.2rem;
    }
    
    /* Search results */
    .search-results-header {
        margin: 1rem 0;
        padding: 0.5rem 0;
    }
    
    .search-results-header h4 {
        color: #ffffff;
        margin: 0;
        font-size: 1rem;
    }
    
    /* Product cards */
    .product-card-simple {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
    }
    
    .product-card-simple:hover {
        background: #2a2a3e;
        border-color: #4a4a6a;
    }
    
    .product-image-simple {
        width: 100%;
        height: 60px;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }
    
    .product-image-simple img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .product-info-simple h6 {
        color: #ffffff;
        font-size: 0.85rem;
        margin: 0 0 0.25rem 0;
        line-height: 1.2;
    }
    
    .product-info-simple .price {
        color: #4ade80;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0 0 0.25rem 0;
    }
    
    /* Product card styles for sidebar */
    .product-card-sidebar {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .product-card-sidebar:hover {
        background: #2a2a3e;
        border-color: #4a4a6a;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .product-title-sidebar {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 12px;
        color: #ffffff;
        line-height: 1.4;
        word-wrap: break-word;
    }
    
    .product-image-container-sidebar {
        text-align: center;
        margin-bottom: 12px;
    }
    
    .product-image-sidebar {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        max-height: 150px;
        object-fit: contain;
        border: 1px solid #2a2a3e;
    }
    
    .product-actions-sidebar {
        display: flex;
        gap: 8px;
        margin-top: 8px;
    }
    
    .product-card-divider {
        border-top: 1px solid #2a2a3e;
        margin: 12px 0;
        opacity: 0.5;
    }
    
    .product-price-sidebar {
        font-weight: 600;
        font-size: 16px;
        color: #4ade80;
        text-align: center;
        margin-top: 8px;
        padding: 4px 8px;
        background: rgba(74, 222, 128, 0.1);
        border-radius: 4px;
        border: 1px solid rgba(74, 222, 128, 0.3);
    }
    
    /* Sidebar image grid styling */
    .sidebar-image-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .sidebar-image-item {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 6px;
        padding: 0.5rem;
        text-align: center;
    }
    
    .sidebar-image-item img {
        border-radius: 4px;
        max-width: 100%;
        height: auto;
    }
    
    .sidebar-image-caption {
        font-size: 0.75rem;
        color: #b0b0b0;
        margin-top: 0.25rem;
        text-align: center;
    }
    
    .sidebar-download-btn {
        font-size: 0.7rem;
        padding: 0.25rem 0.5rem;
        margin-top: 0.25rem;
    }
    
    /* Enhanced product display styling */
    .price-section {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0.25rem 0;
    }
    
    .current-price {
        color: #4ade80;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .list-price {
        color: #b0b0b0;
        text-decoration: line-through;
        font-size: 0.8rem;
    }
    
    .rating-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0.25rem 0;
    }
    
    .stars {
        color: #fbbf24;
        font-size: 0.8rem;
    }
    
    .brand {
        color: #b0b0b0;
        font-size: 0.8rem;
        font-style: italic;
    }
    
    .view-product-btn {
        display: inline-block;
        background: #3b82f6;
        color: white;
        text-decoration: none;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-top: 0.25rem;
        transition: background 0.2s ease;
    }
    
    .view-product-btn:hover {
        background: #2563eb;
        color: white;
        text-decoration: none;
    }
    
    /* Raw data expander styling */
    .raw-data-expander {
        margin-top: 0.5rem;
        border-top: 1px solid #2a2a3e;
        padding-top: 0.5rem;
    }
    
    .raw-data-expander .streamlit-expanderHeader {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 6px;
        color: #b0b0b0;
        font-size: 0.85rem;
        padding: 0.5rem 0.75rem;
        transition: all 0.2s ease;
    }
    
    .raw-data-expander .streamlit-expanderHeader:hover {
        background: #2a2a3e;
        border-color: #4a4a6a;
        color: #ffffff;
    }
    
    .raw-data-expander .streamlit-expanderContent {
        background: #0f0f23;
        border: 1px solid #2a2a3e;
        border-radius: 6px;
        margin-top: 0.5rem;
        padding: 1rem;
    }
    
    /* JSON display styling */
    .raw-data-json {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 4px;
        padding: 1rem;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.8rem;
        line-height: 1.4;
        overflow-x: auto;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .product-info-simple small {
        color: #b0b0b0;
        font-size: 0.75rem;
    }
    
    /* Chat container */
    .chat-container-simple {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #2a2a3e;
    }
    
    .chat-container-simple h2 {
        color: #ffffff;
        margin: 0 0 1rem 0;
        font-size: 1.5rem;
    }
    
    /* Message content */
    .message-content {
        color: #ffffff;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* Typing indicator */
    .typing-indicator-simple {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 0.5rem 0;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4a4a6a;
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { opacity: 0.3; }
        30% { opacity: 1; }
    }
    
    /* Simple footer */
    .simple-footer {
        text-align: center;
        padding: 1rem 0;
        color: #6b7280;
        font-size: 0.9rem;
    }
    
    /* Streamlit overrides for dark theme */
    .stTextInput, .stTextArea, .stSelectbox {
        background: #1a1a2e !important;
        border: 1px solid #2a2a3e !important;
        color: #ffffff !important;
    }
    
    .stTextInput input, .stTextArea textarea {
        background: #1a1a2e !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #6b7280 !important;
    }
    
    /* Chat input styling */
    .stChatInput {
        background: #1a1a2e !important;
        border: 1px solid #2a2a3e !important;
        border-radius: 8px !important;
    }
    
    .stChatInput input {
        background: transparent !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    .stChatInput input::placeholder {
        color: #6b7280 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: #4a4a6a !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: #5a5a7a !important;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: #1a1a2e !important;
        border: 1px solid #2a2a3e !important;
        border-radius: 8px !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Sidebar background */
    .css-1d391kg {
        background: #0f0f23 !important;
    }
    
    /* Main content area */
    .main .block-container {
        background: transparent !important;
    }
    
    /* Remove default backgrounds */
    .stApp > div {
        background: transparent !important;
    }
    
    /* Alert styling */
    .stAlert {
        background: #1a1a2e !important;
        border: 1px solid #2a2a3e !important;
        color: #ffffff !important;
    }
    
    /* Success/Error/Warning boxes */
    .stAlert[data-baseweb="notification"] {
        background: #1a1a2e !important;
        border: 1px solid #2a2a3e !important;
        color: #ffffff !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        color: #4a4a6a !important;
    }
    
    /* Sidebar placeholder */
    .sidebar-placeholder {
        background: #1a1a2e;
        border: 1px solid #2a2a3e;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .sidebar-placeholder p {
        color: #6b7280;
        font-size: 0.9rem;
        margin: 0;
    }
</style>
"""
