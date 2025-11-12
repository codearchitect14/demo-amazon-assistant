'use client';

import { useState, useCallback } from 'react';
import { ChatMessage, Product, apiClient } from '../lib/api-client';
import { extractProductsFromContext } from '../lib/product-extraction';

export function useChatSimulation(initialMessages: ChatMessage[]) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: content.trim(),
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      let fullResponse = '';
      let contextData = '';

      // Prepare conversation history for context
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Stream the response with conversation history
      for await (const chunk of apiClient.sendChatMessageStream({
        query: content.trim(),
        conversation_history: conversationHistory,
        top_k: 5,
        retrieval_method: 'title_first'
      })) {
        if (chunk.type === 'token' && chunk.content) {
          fullResponse += chunk.content;
          
          // Update the assistant message in real-time
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            
            if (lastMessage && lastMessage.role === 'assistant') {
              // Update existing assistant message
              lastMessage.content = fullResponse;
            } else {
              // Add new assistant message
              newMessages.push({
                id: (Date.now() + 1).toString(),
                content: fullResponse,
                role: 'assistant',
                timestamp: new Date()
              });
            }
            
            return newMessages;
          });
        } else if (chunk.type === 'complete' && chunk.context) {
          contextData = chunk.context;
        }
      }

      // Extract products from context
      if (contextData) {
        const extractedProducts = extractProductsFromContext(contextData);
        if (extractedProducts.length > 0) {
          setProducts(prev => {
            const newProducts = [...prev, ...extractedProducts];
            // Keep only the last 10 products
            return newProducts.slice(-10);
          });
        }
      }

      // Ensure we have a final assistant message
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        
        if (!lastMessage || lastMessage.role !== 'assistant') {
          newMessages.push({
            id: (Date.now() + 1).toString(),
            content: fullResponse || "I'm here to help you find great products!",
            role: 'assistant',
            timestamp: new Date()
          });
        }
        
        return newMessages;
      });

    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: "I'm having trouble connecting right now, but I'm still here to help! Try asking me about products you're interested in.",
        role: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, [messages]);

  const clearProducts = useCallback(() => {
    setProducts([]);
  }, []);

  const removeProduct = useCallback((productId: string) => {
    setProducts(prev => prev.filter(p => p.id !== productId));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  return {
    messages,
    isTyping,
    products,
    sendMessage,
    clearProducts,
    removeProduct,
    clearMessages
  };
}
