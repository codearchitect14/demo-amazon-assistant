# Product Extraction and Showcasing in Next.js Sidebar

## Overview

This document explains how the Next.js frontend extracts and showcases products in the sidebar after AI message streaming is complete, similar to the Streamlit app.

## How It Works

### 1. Streaming Response Processing

The `use-chat.ts` hook processes streaming responses from the backend:

```typescript
// In use-chat.ts
for await (const chunk of apiService.sendChatMessageStream(request)) {
  switch (chunk.type) {
    case 'context':
      // Extract products from context chunk
      const products = extractProductsFromContext(chunk.content);
      if (products.length > 0) {
        addProducts(products);
      }
      break;
    
    case 'complete':
      // Fallback: extract from completion chunk if not already done
      if (!productsExtracted && chunk.context) {
        const products = extractProductsFromContext(chunk.context);
        addProducts(products);
      }
      break;
  }
}
```

### 2. Product Extraction Logic

The `extractProductsFromContext` function in `api.ts` extracts products from the context:

```typescript
export function extractProductsFromContext(context: string): Product[] {
  const products: Product[] = [];
  
  // Split context into sections
  const sections = context.split('\n\n');
  
  for (const section of sections) {
    if (section.includes('Title:') || section.includes('Price:')) {
      const product: Product = { title: '', price: '' };
      
      // Extract title
      const titleMatch = section.match(/Title[:\s]+([^\n|]+)/i);
      if (titleMatch) {
        product.title = cleanProductTitle(titleMatch[1].trim());
      }
      
      // Extract price
      const priceMatch = section.match(/Price[:\s]+([^\n|]+)/i);
      if (priceMatch) {
        product.price = cleanProductPrice(priceMatch[1].trim());
      }
      
      // Extract image URL
      const imageMatch = section.match(/https?:\/\/[^\s<>\"]+\.(?:jpg|jpeg|png|gif|webp)/i);
      if (imageMatch) {
        product.image = imageMatch[0];
      }
      
      // Only add if both title and price are present
      if (product.title && product.price) {
        products.push(product);
      }
    }
  }
  
  return products;
}
```

### 3. Sidebar Display

The sidebar component displays extracted products with search functionality:

```typescript
// In sidebar.tsx
export function Sidebar({ products, isLoading }: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  
  // Filter products based on search
  const filteredProducts = searchQuery
    ? products.filter(product =>
        product.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.price.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : products;
    
  return (
    <div className="w-full lg:w-96 xl:w-[420px] bg-white/30 backdrop-blur-xl">
      {/* Header with product count */}
      <div className="p-6 border-b border-white/20">
        <h2 className="text-xl font-bold">Product Gallery</h2>
        <p className="text-sm text-slate-600">
          {isLoading ? 'Extracting products...' : `${filteredProducts.length} products found`}
        </p>
      </div>
      
      {/* Search bar */}
      <div className="p-6">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search products..."
          className="w-full px-4 py-2 rounded-lg"
        />
      </div>
      
      {/* Products grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              Extracting products...
            </h3>
            <p className="text-slate-500 text-sm">
              AI is analyzing the conversation for product information
            </p>
          </div>
        ) : filteredProducts.length > 0 ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {filteredProducts.map((product, index) => (
              <ProductCard key={index} product={product} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              {searchQuery ? 'No products found' : 'No products yet'}
            </h3>
            <p className="text-slate-500 text-sm">
              {searchQuery 
                ? `Try adjusting your search terms for "${searchQuery}"`
                : 'Start a conversation to discover products!'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
```

## Key Features

### 1. Real-time Product Extraction
- Products are extracted as soon as the context chunk is received
- Fallback extraction from completion chunk if needed
- Multiple extraction attempts to ensure no products are missed

### 2. Loading States
- Shows "Extracting products..." when streaming is in progress
- Displays loading spinner in sidebar during extraction
- Updates product count in real-time

### 3. Search Functionality
- Search through extracted products by title or price
- Real-time filtering as you type
- Clear search button to reset filters

### 4. Product Cards
- Displays product title, price, and image
- Responsive grid layout (1 column on mobile, 2 on desktop)
- Smooth animations when products are added

### 5. Error Handling
- Graceful handling of extraction failures
- Fallback mechanisms if context format changes
- Console logging for debugging

## Context Format

The backend sends context in this format:

```
Document 1:
Metadata: Title: Wireless Bluetooth Headphones | Price: $89.99 | Category: Electronics
Content: High-quality wireless headphones with noise cancellation

Document 2:
Metadata: Title: Ergonomic Office Chair | Price: $299.99 | Category: Furniture
Content: Comfortable office chair with adjustable features
```

The extraction logic looks for:
- `Title:` followed by product name
- `Price:` followed by price value
- Image URLs in the content

## Testing

You can test the product extraction logic using the test script:

```bash
node test_product_extraction.js
```

This will verify that the extraction logic correctly handles different context formats.

## Usage

1. Start the application: `python run_next_app.py`
2. Open the Next.js frontend in your browser
3. Ask questions about products (e.g., "Show me wireless headphones")
4. Watch as products are automatically extracted and displayed in the sidebar
5. Use the search bar to filter products
6. Products persist across conversations until you clear the chat

The sidebar will automatically update with new products after each AI response, just like in the Streamlit app! 