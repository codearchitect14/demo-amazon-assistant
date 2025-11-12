export interface Product {
  id: string;
  title: string;
  price: number;
  image: string;
  category: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export const dummyProducts: Product[] = [
  {
    id: '1',
    title: 'Wireless Bluetooth Headphones',
    price: 89.99,
    image: '/wireless-headphones.png',
    category: 'Electronics'
  },
  {
    id: '2',
    title: 'Smart Fitness Watch',
    price: 199.99,
    image: '/fitness-smartwatch.png',
    category: 'Wearables'
  },
  {
    id: '3',
    title: 'Organic Coffee Beans',
    price: 24.99,
    image: '/pile-of-coffee-beans.png',
    category: 'Food'
  },
  {
    id: '4',
    title: 'Ergonomic Office Chair',
    price: 299.99,
    image: '/ergonomic-office-chair.png',
    category: 'Furniture'
  },
  {
    id: '5',
    title: 'Portable Phone Charger',
    price: 39.99,
    image: '/placeholder-218ll.png',
    category: 'Electronics'
  },
  {
    id: '6',
    title: 'Yoga Mat Premium',
    price: 49.99,
    image: '/rolled-yoga-mat.png',
    category: 'Fitness'
  },
  {
    id: '7',
    title: 'Stainless Steel Water Bottle',
    price: 19.99,
    image: '/reusable-water-bottle.png',
    category: 'Lifestyle'
  },
  {
    id: '8',
    title: 'LED Desk Lamp',
    price: 79.99,
    image: '/modern-desk-lamp.png',
    category: 'Home'
  },
  {
    id: '9',
    title: 'Wireless Mouse',
    price: 29.99,
    image: '/wireless-mouse.png',
    category: 'Electronics'
  },
  {
    id: '10',
    title: 'Plant-Based Protein Powder',
    price: 34.99,
    image: '/protein-powder-assortment.png',
    category: 'Health'
  }
];

export const dummyChatMessages: ChatMessage[] = [
  {
    id: '1',
    content: 'Hello! I\'m your AI shopping assistant. How can I help you find the perfect product today?',
    role: 'assistant',
    timestamp: new Date(Date.now() - 300000)
  },
  // {
  //   id: '2',
  //   content: 'I\'m looking for some good headphones for working out',
  //   role: 'user',
  //   timestamp: new Date(Date.now() - 240000)
  // },
  // {
  //   id: '3',
  //   content: 'Great choice! For workouts, I\'d recommend our Wireless Bluetooth Headphones. They\'re sweat-resistant, have excellent sound quality, and stay secure during exercise. They\'re currently priced at $89.99. Would you like to know more about their features?',
  //   role: 'assistant',
  //   timestamp: new Date(Date.now() - 180000)
  // }
];

export const assistantResponses = [
  "I'd be happy to help you find the perfect product! What are you looking for today?",
  "Based on your preferences, I can recommend several great options. Let me show you some products that might interest you.",
  "That's a great choice! This product has excellent reviews and offers great value for money.",
  "I can help you compare different options. What's most important to you - price, quality, or specific features?",
  "Let me search our catalog for products that match your criteria. I'll find the best options for you!",
  "Would you like me to explain more about any of these products or help you find something else?",
  "I notice you're interested in electronics. We have some amazing deals on tech products right now!",
  "That's a popular item! Many customers have been very satisfied with this purchase."
];
