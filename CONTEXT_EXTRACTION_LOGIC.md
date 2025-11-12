# Context Extraction Logic - Code Flow Analysis

## Overview
This document explains the step-by-step logic of how context is extracted and processed in the RAG demo application.

---

## 1. Main Flow: User Input → API Call → Context Extraction

### Step 1: User Input Capture
```python
# In main() function, lines 783-786
if prompt := st.chat_input("Ask me about products..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.rerun()
```
**Logic**: Captures user input and adds it to chat history

### Step 2: Trigger Assistant Response
```python
# Lines 789-793
if st.session_state.chat_history and st.session_state.chat_history[-1]['role']=='user':
    user_msg = st.session_state.chat_history[-1]['content']
    placeholder = st.empty()
    placeholder.markdown("<div class='typing-indicator'>🤖 AI is thinking...</div>")
```
**Logic**: Checks if last message is from user, then prepares for AI response

---

## 2. Streaming Response Processing

### Step 3: Async Response Generation
```python
# Lines 795-825
async def get_response():
    full, raw = "", {"context":"","metadata":{}}
    async for chunk in stream_chat_response(user_msg, st.session_state.session_id):
        if chunk.get("type") == "token":
            full += chunk.get("content","")
            # Display with typing animation
        elif chunk.get("type") == "complete":
            raw = chunk  # ← CRITICAL: This captures the context
            break
    return full, raw
```

**Logic Breakdown**:
1. **Initialize variables**: `full` (accumulated response), `raw` (complete chunk data)
2. **Stream processing**: Iterate through API response chunks
3. **Token handling**: Accumulate text for real-time display
4. **Complete handling**: Capture the "complete" chunk which contains context

### Step 4: API Client Call
```python
# In stream_chat_response() function, lines 585-635
async def stream_chat_response(query, session_id, top_k=5, retrieval_method="title_first"):
    api_client = get_api_client()
    async for chunk in api_client.send_chat_message_stream(
        query=query, session_id=session_id, top_k=top_k, retrieval_method=retrieval_method
    ):
        yield chunk
```

**Logic**: Makes streaming API call and yields each chunk

---

## 3. Context Extraction Process

### Step 5: Extract Context from Raw Data
```python
# Lines 830-835
full_resp, raw_data = asyncio.run(get_response())
st.session_state.chat_history.append({"role":"assistant","content":full_resp})

# Extract products
ctx = raw_data.get("context", "")  # ← EXTRACT CONTEXT HERE
if ctx:
    new_ps = extract_products_from_context(ctx)  # ← PROCESS CONTEXT
    if new_ps:
        st.session_state.products.extend(new_ps)
        st.session_state.products = st.session_state.products[-10:]
```

**Logic**:
1. **Get context**: Extract context string from raw_data
2. **Process context**: Call `extract_products_from_context()`
3. **Store products**: Add to session state, keep last 10

---

## 4. Product Extraction Logic

### Step 6: Context Parsing Function
```python
# Lines 661-675
def extract_products_from_context(context: str) -> List[Dict]:
    products = []
    for section in context.split("\n\n"):  # ← SPLIT BY DOUBLE NEWLINES
        if "Title:" in section or "Price:" in section:  # ← CHECK FOR PRODUCT DATA
            prod = {}
            # Extract title
            m = re.search(r"Title[:\s]+([^\n]+)", section, re.IGNORECASE)
            if m: prod["title"] = clean_product_title(m.group(1).strip())
            # Extract price
            m = re.search(r"Price[:\s]+([^\n]+)", section, re.IGNORECASE)
            if m: prod["price"] = clean_product_price(m.group(1).strip())
            # Extract image URL
            m = re.search(r"https?://[^\s<>\"]+\.(?:jpg|jpeg|png|gif|webp)", section)
            if m: prod["image"] = sanitizer.sanitize_url(m.group(0))
            if prod: products.append(prod)  # ← ADD IF ANY DATA FOUND
    return products
```

**Logic Breakdown**:
1. **Split context**: Divide by double newlines to get sections
2. **Check for products**: Look for "Title:" or "Price:" in section
3. **Extract data**: Use regex to find title, price, and image URL
4. **Clean data**: Apply cleaning functions to each field
5. **Return products**: List of cleaned product dictionaries

---

## 5. Data Cleaning Functions

### Step 7: Title Cleaning
```python
# Lines 638-641
def clean_product_title(title: str) -> str:
    title = re.sub(r"^Product[:\-]?\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^Item[:\-]?\s*", "", title, flags=re.IGNORECASE)
    return sanitizer.sanitize_string(title.rstrip(".,;:!?"), 200)
```

**Logic**:
1. **Remove prefixes**: Strip "Product:" or "Item:" from start
2. **Remove punctuation**: Strip trailing punctuation
3. **Sanitize**: Apply general string sanitization (max 200 chars)

### Step 8: Price Cleaning
```python
# Lines 643-659
def clean_product_price(price: str) -> str:
    price = re.sub(r"^(Price|Cost)[:\-]?\s*", "", price, flags=re.IGNORECASE).rstrip(".,;:!?")
    if price.replace(".", "").replace(",", "").isdigit() and not price.startswith("$"):
        price = f"${price}"  # ← ADD DOLLAR SIGN IF MISSING
    if price.startswith("$"):
        try:
            num = price[1:].replace(",", "")
            if "." in num:
                i, d = num.split(".")
                price = f"${int(i):,}.{d}"  # ← FORMAT WITH COMMAS
            else:
                price = f"${int(num):,}"
        except:
            pass
    return price
```

**Logic**:
1. **Remove prefixes**: Strip "Price:" or "Cost:" from start
2. **Add currency**: Add "$" if missing and it's a number
3. **Format numbers**: Add commas for thousands (e.g., $1,299.99)
4. **Handle decimals**: Preserve decimal places

---

## 6. Session State Management

### Step 9: Product Storage
```python
# Lines 833-836
if ctx:
    new_ps = extract_products_from_context(ctx)
    if new_ps:
        st.session_state.products.extend(new_ps)  # ← ADD NEW PRODUCTS
        st.session_state.products = st.session_state.products[-10:]  # ← KEEP LAST 10
```

**Logic**:
1. **Extend list**: Add new products to existing list
2. **Limit size**: Keep only last 10 products (sliding window)
3. **Auto-update**: Sidebar automatically shows updated products

---

## 7. Sidebar Display Logic

### Step 10: Product Gallery Rendering
```python
# Lines 720-740
if filtered_products:
    st.markdown(f"<h4>📦 Products ({len(filtered_products)})</h4>")
    prods = filtered_products[-10:]  # Show last 10 filtered products
    for i in range(0, len(prods), 2):  # ← DISPLAY IN 2-COLUMN GRID
        cols = st.columns(2)
        for idx, col in enumerate(cols):
            if i+idx < len(prods):
                p = prods[i+idx]
                col.markdown(
                    f"<div class='product-card'>"
                    f"<img src='{p.get('image','https://via.placeholder.com/150')}' />"
                    f"<h5>{p.get('title','Unknown')}</h5>"
                    f"<p>{p.get('price','N/A')}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )
```

**Logic**:
1. **Check products**: Only render if products exist
2. **Grid layout**: Display in 2-column grid
3. **Product cards**: Show image, title, and price
4. **Fallback values**: Use placeholders for missing data

---

## 8. Search Functionality

### Step 11: Product Filtering
```python
# Lines 700-715
filtered_products = st.session_state.products
if search_query:
    search_lower = search_query.lower()
    filtered_products = [
        p for p in st.session_state.products
        if (search_lower in p.get('title', '').lower() or 
            search_lower in p.get('price', '').lower())
    ]
```

**Logic**:
1. **Get search term**: From user input
2. **Case-insensitive**: Convert to lowercase for comparison
3. **Filter products**: Match against title or price
4. **Update display**: Show only matching products

---

## Data Flow Summary

```
User Input → API Call → Streaming Response → Context Extraction → Product Parsing → Data Cleaning → Session Storage → UI Update
```

### Key Data Structures:

**Raw API Response**:
```json
{
  "type": "complete",
  "context": "Title: Ergonomic Office Chair\nPrice: $299.99\nhttps://example.com/chair.jpg",
  "metadata": {...}
}
```

**Extracted Product**:
```json
{
  "title": "Ergonomic Office Chair",
  "price": "$299.99",
  "image": "https://example.com/chair.jpg"
}
```

**Session State**:
```python
st.session_state.products = [
    {"title": "Product 1", "price": "$29.99", "image": "url1"},
    {"title": "Product 2", "price": "$49.99", "image": "url2"},
    # ... up to 10 products
]
```

---

## Error Handling

### Context Extraction Errors:
- **Empty context**: No products extracted
- **Invalid format**: Regex patterns don't match
- **Sanitization failures**: Invalid URLs or text

### Session State Errors:
- **Memory limits**: Products list gets truncated
- **Display errors**: Missing product data shows fallbacks

### API Errors:
- **Network issues**: Connection failures
- **Streaming errors**: Incomplete responses
- **Timeout errors**: Long-running requests

---

## Performance Considerations

1. **Streaming**: Real-time response display
2. **Regex efficiency**: Fast pattern matching
3. **Session limits**: Only 10 products in memory
4. **UI updates**: Automatic re-rendering
5. **Search optimization**: Case-insensitive filtering 