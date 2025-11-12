import { Product } from './api-client';

export function extractProductsFromContext(context: string): Product[] {
  const products: Product[] = [];
  
  // Split context by double newlines to get sections
  const sections = context.split('\n\n');
  
  for (const section of sections) {
    if (section.includes('Title:') || section.includes('Price:')) {
      const product: Partial<Product> = {};
      
      // Extract title
      const titleMatch = section.match(/Title[:\s]+([^\n]+)/i);
      if (titleMatch) {
        product.title = cleanProductTitle(titleMatch[1].trim());
      }
      
      // Extract price
      const priceMatch = section.match(/Price[:\s]+([^\n]+)/i);
      if (priceMatch) {
        product.price = cleanProductPrice(priceMatch[1].trim());
      }
      
      // Extract image URL
      const imageMatch = section.match(/https?:\/\/[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)/i);
      if (imageMatch) {
        product.image = sanitizeUrl(imageMatch[0]);
      }
      
      // Generate ID and add to products if we have at least title or price
      if (product.title || product.price) {
        product.id = generateProductId(product.title || 'product');
        product.category = inferCategory(product.title || '');
        
        // Set defaults for missing fields
        if (!product.title) product.title = 'Unknown Product';
        if (!product.price) product.price = 'Price not available';
        if (!product.image) product.image = '/placeholder.svg?height=150&width=150&text=No+Image';
        
        products.push(product as Product);
      }
    }
  }
  
  return products;
}

function cleanProductTitle(title: string): string {
  // Remove common prefixes
  title = title.replace(/^(Product|Item)[:\-]?\s*/i, '');
  
  // Remove trailing punctuation
  title = title.replace(/[.,;:!?]+$/, '');
  
  // Sanitize and limit length
  return sanitizeString(title, 200);
}

function cleanProductPrice(price: string): string {
  // Remove common prefixes
  price = price.replace(/^(Price|Cost)[:\-]?\s*/i, '');
  
  // Remove trailing punctuation
  price = price.replace(/[.,;:!?]+$/, '');
  
  // Add dollar sign if missing and it's a number
  if (price.replace(/[.,]/g, '').match(/^\d+$/) && !price.startsWith('$')) {
    price = `$${price}`;
  }
  
  // Format price with commas
  if (price.startsWith('$')) {
    try {
      const numStr = price.slice(1).replace(/,/g, '');
      if (numStr.includes('.')) {
        const [integer, decimal] = numStr.split('.');
        price = `$${parseInt(integer).toLocaleString()}.${decimal}`;
      } else {
        price = `$${parseInt(numStr).toLocaleString()}`;
      }
    } catch (e) {
      // Keep original if formatting fails
    }
  }
  
  return price;
}

function sanitizeUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    // Basic URL validation
    if (urlObj.protocol === 'http:' || urlObj.protocol === 'https:') {
      return url;
    }
  } catch (e) {
    // Invalid URL
  }
  return '/placeholder.svg?height=150&width=150&text=Invalid+Image';
}

function sanitizeString(str: string, maxLength: number): string {
  // Remove potentially dangerous characters
  str = str.replace(/[<>\"'&]/g, '');
  
  // Limit length
  if (str.length > maxLength) {
    str = str.substring(0, maxLength - 3) + '...';
  }
  
  return str.trim();
}

function generateProductId(title: string): string {
  return `product_${Date.now()}_${title.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 10)}`;
}

function inferCategory(title: string): string {
  const titleLower = title.toLowerCase();
  
  if (titleLower.includes('headphone') || titleLower.includes('speaker') || titleLower.includes('audio')) {
    return 'Electronics';
  }
  if (titleLower.includes('watch') || titleLower.includes('fitness') || titleLower.includes('tracker')) {
    return 'Wearables';
  }
  if (titleLower.includes('chair') || titleLower.includes('desk') || titleLower.includes('furniture')) {
    return 'Furniture';
  }
  if (titleLower.includes('coffee') || titleLower.includes('food') || titleLower.includes('drink')) {
    return 'Food & Beverage';
  }
  if (titleLower.includes('yoga') || titleLower.includes('exercise') || titleLower.includes('gym')) {
    return 'Fitness';
  }
  
  return 'General';
}
