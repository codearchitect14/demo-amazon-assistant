'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2 } from 'lucide-react';
import { ChatMessageComponent } from './chat-message';
import { TypingIndicator } from './typing-indicator';
import { ChatMessage } from '../lib/api-client';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isTyping: boolean;
  onSendMessage: (message: string) => Promise<void>;
}

export function ChatInterface({ messages, isTyping, onSendMessage }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, isTyping]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isSending) return;

    setIsSending(true);
    try {
      await onSendMessage(inputValue);
      setInputValue('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white/20 backdrop-blur-xl shadow-2xl h-full border-l border-white/30">
      {/* Compact Chat Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-5 border-b border-white/30 bg-gradient-to-r from-white/60 via-white/50 to-white/40 backdrop-blur-xl shadow-lg"
      >
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
            <span className="text-xl">🤖</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
              AI Shopping Assistant
            </h1>
            <p className="text-slate-600 text-sm font-medium">
              Ask me anything about products, get recommendations, or browse our catalog!
            </p>
          </div>
        </div>
      </motion.div>

      {/* Scrollable Messages Container - Fixed horizontal overflow */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-4"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(148, 163, 184, 0.3) transparent' }}
      >
        <AnimatePresence mode="popLayout">
          {messages.map((message, index) => (
            <ChatMessageComponent
              key={message.id}
              message={message}
              index={index}
            />
          ))}
          
          {isTyping && (
            <motion.div
              key="typing"
              className="flex items-start space-x-3"
            >
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-slate-600 to-slate-700 flex items-center justify-center shadow-lg">
                <Loader2 className="w-4 h-4 text-white animate-spin" />
              </div>
              <TypingIndicator />
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Compact Input Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="p-4 border-t border-white/30 bg-gradient-to-r from-white/70 via-white/60 to-white/50 backdrop-blur-xl shadow-2xl"
      >
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <motion.input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask about products, get recommendations..."
              disabled={isSending}
              animate={{
                boxShadow: isFocused 
                  ? '0 0 0 3px rgba(59, 130, 246, 0.15), 0 8px 25px rgba(0, 0, 0, 0.1)' 
                  : '0 0 0 0px rgba(59, 130, 246, 0.15), 0 4px 12px rgba(0, 0, 0, 0.08)',
                scale: isFocused ? 1.01 : 1
              }}
              transition={{ duration: 0.2 }}
              className="w-full px-4 py-3 bg-white/90 backdrop-blur-sm border-2 border-white/40 rounded-xl focus:outline-none focus:border-blue-400/60 transition-all duration-300 text-slate-700 placeholder-slate-400 disabled:opacity-50 text-base font-medium shadow-lg"
            />
            <motion.div
              animate={{
                opacity: isFocused ? 1 : 0,
                scale: isFocused ? 1 : 0.8
              }}
              className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-400/20 to-purple-400/20 -z-10 blur-xl"
            />
          </div>
          <motion.button
            type="submit"
            disabled={!inputValue.trim() || isSending}
            whileHover={{ scale: 1.05, y: -1 }}
            whileTap={{ scale: 0.95 }}
            animate={{
              boxShadow: !inputValue.trim() || isSending
                ? '0 4px 12px rgba(0, 0, 0, 0.1)'
                : '0 8px 20px rgba(59, 130, 246, 0.3)'
            }}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 focus:outline-none transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 font-semibold border border-blue-400/30"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span className="hidden sm:inline text-sm">Send</span>
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
}
