# RAG Chatbot with Product Recommendations

A comprehensive Streamlit application that integrates with your RAG pipeline and product recommendation system.

## 🚀 Features

### Core Functionality
- **RAG Chat Interface**: Ask questions about products and get intelligent responses
- **Real-time Context Display**: See the documents used to generate responses
- **Product Recommendations**: Search and filter products with intelligent recommendations
- **API Integration**: Full integration with your FastAPI backend

### UI Components

#### Left Sidebar - Configuration
- **Retrieval Settings**: Choose retrieval method and number of documents
- **Product Filters**: Filter by brand, category, and price range
- **API Status**: Real-time connection status
- **Clear Chat**: Reset conversation history

#### Main Chat Area
- **Chat Interface**: Modern chat UI with message history
- **Response Details**: Expandable metadata for each response
- **Loading States**: Visual feedback during processing

#### Right Sidebar - Context & Data
- **Retrieved Context**: Shows documents used for responses
- **Response Metadata**: Detailed information about the RAG process
- **Product Recommendations**: Search and display product recommendations

## 🛠️ Setup & Running

### Option 1: Run Both Services Together
```bash
cd rag-demo
python run_app.py
```

### Option 2: Run Services Separately

#### Start the API Server
```bash
cd rag-demo
uvicorn app.api:app --host 0.0.0.0 --port 3001 --reload
```

#### Start the Streamlit App
```bash
cd rag-demo
streamlit run app/app.py --server.port 8501
```

## 📱 Access the Application

- **Streamlit App**: http://localhost:8501
- **API Server**: http://localhost:3001
- **API Documentation**: http://localhost:3001/docs

## 🎯 How to Use

### 1. Chat with RAG
1. Type your question in the chat input
2. Choose retrieval method and settings in the sidebar
3. View the response and context in the right sidebar
4. Expand "Response Details" to see metadata

### 2. Get Product Recommendations
1. Enter a product search query in the right sidebar
2. Apply filters (brand, category, price range)
3. Click "Get Recommendations"
4. Browse the recommended products

### 3. Configure Settings
- **Retrieval Method**: Choose from available methods (multi, weighted, title, reviews, qa, title_first)
- **Top-K**: Set number of documents to retrieve (1-20)
- **Filters**: Apply product filters for recommendations

## 🔧 Configuration

### Environment Variables
The app uses the same configuration as your API:
- `GROQ_API_KEY`: Required for LLM responses
- `API_URL`: Backend API URL (default: http://localhost:3001)
- Other RAG and embedding configurations

### API Endpoints Used
- `GET /health`: Health check
- `GET /retrieval-methods`: Available retrieval methods
- `GET /filters`: Available product filters
- `POST /chat`: Send chat messages
- `POST /recommend`: Get product recommendations

## 📊 Data Display

### Context Information
The right sidebar shows:
- **Retrieved Documents**: Raw text used for response generation
- **Response Metadata**: Detailed information about the RAG process
- **Product Recommendations**: Filtered product suggestions

### Response Details
Each assistant response includes:
- Retrieval method used
- Number of documents retrieved
- Processing time
- Additional metadata from the RAG pipeline

## 🎨 UI Features

### Responsive Design
- Wide layout for better data visibility
- Collapsible sections for detailed information
- Loading spinners and error handling

### Visual Elements
- Emoji icons for better UX
- Color-coded status indicators
- Product cards with images and details
- Expandable metadata sections

## 🔍 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Check if the API server is running on port 3001
   - Verify environment variables are set correctly

2. **No Responses**
   - Ensure `GROQ_API_KEY` is configured
   - Check API logs for errors

3. **No Product Recommendations**
   - Verify the recommendation engine is working
   - Check if product data is available

### Debug Information
- API status is shown in the sidebar
- Error messages are displayed in the chat
- Response metadata includes debugging information

## 🚀 Next Steps

### Potential Enhancements
- Add user authentication
- Implement conversation history persistence
- Add more product filters
- Integrate with external product APIs
- Add export functionality for conversations

### Customization
- Modify the UI theme in `app.py`
- Add new API endpoints in `api.py`
- Customize the recommendation engine
- Add new retrieval methods

## 📝 Notes

- The app requires both the API server and Streamlit to be running
- All API calls include proper error handling
- The interface is designed to be user-friendly for both technical and non-technical users
- The right sidebar provides transparency into the RAG process 