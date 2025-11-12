export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface Product {
  id: string;
  title: string;
  price: string;
  image: string;
  category?: string;
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  conversation_history?: Array<{ role: 'user' | 'assistant'; content: string }>;
  top_k?: number;
  retrieval_method?: 'title_first' | 'multi' | 'hybrid' | 'semantic';
  use_advanced_features?: boolean;
}

export interface ChatResponse {
  question: string;
  answer: string;
  context: string;
  intent: any;
  metadata: any;
}

export interface StreamChunk {
  type: 'token' | 'context' | 'complete' | 'error';
  content?: string;
  context?: string;
  intent?: any;
  metadata?: any;
  message?: string;
}

class APIClient {
  private baseUrl: string;
  private sessionId: string;

  constructor(baseUrl: string = 'https://5516b4c78c4d.ngrok-free.app') {
    this.baseUrl = baseUrl;
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true', // Skip ngrok browser warning
        },
        body: JSON.stringify({
          ...request,
          session_id: request.session_id || this.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat API error:', error);
      // Return dummy data as fallback
      return {
        question: request.query,
        answer: "I'm having trouble connecting to the server right now. Here are some great products I can recommend based on your query!",
        context: this.generateDummyContext(),
        intent: { type: 'product_search' },
        metadata: { fallback: true }
      };
    }
  }

  async *sendChatMessageStream(request: ChatRequest): AsyncGenerator<StreamChunk, void, unknown> {
    try {
      const response = await fetch(`${this.baseUrl}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true', // Skip ngrok browser warning
        },
        body: JSON.stringify({
          ...request,
          session_id: request.session_id || this.sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data as StreamChunk;
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream API error:', error);
      // Yield dummy streaming data as fallback
      yield* this.generateDummyStream(request.query);
    }
  }

  private generateDummyContext(): string {
    const dummyProducts = [
      "Title: Wireless Bluetooth Headphones\nPrice: $89.99\nhttps://example.com/headphones.jpg",
      "Title: Smart Fitness Watch\nPrice: $199.99\nhttps://example.com/watch.jpg",
      "Title: Ergonomic Office Chair\nPrice: $299.99\nhttps://example.com/chair.jpg"
    ];
    return dummyProducts.join('\n\n');
  }

  private async *generateDummyStream(query: string): AsyncGenerator<StreamChunk, void, unknown> {
    const responses = [
      "I'd be happy to help you find the perfect product! ",
      "Based on your query, I can recommend several great options. ",
      "Let me show you some products that match what you're looking for."
    ];

    // Simulate streaming tokens
    for (const response of responses) {
      for (const char of response) {
        yield { type: 'token', content: char };
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }

    // Yield complete chunk with context
    yield {
      type: 'complete',
      context: this.generateDummyContext(),
      metadata: { fallback: true, query }
    };
  }

  async getHealthStatus() {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        headers: {
          'ngrok-skip-browser-warning': 'true', // Skip ngrok browser warning
        }
      });
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'offline', message: 'API unavailable' };
    }
  }
}

export const apiClient = new APIClient();
