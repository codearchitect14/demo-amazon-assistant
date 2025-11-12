'use client';

import { motion } from 'framer-motion';
import { Sidebar } from '../components/sidebar';
import { ChatInterface } from '../components/chat-interface';
import { useChatSimulation } from '../hooks/use-chat-simulation';
import { dummyChatMessages } from '../data/dummy-data';

export default function Home() {
  const { 
    messages, 
    isTyping, 
    products, 
    sendMessage, 
    clearProducts, 
    removeProduct,
    clearMessages
  } = useChatSimulation(dummyChatMessages);

  return (
    <div className="h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 overflow-hidden">
      <div className="flex flex-col lg:flex-row h-full">
        {/* Mobile Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:hidden p-4 bg-white/40 backdrop-blur-lg border-b border-white/20 flex-shrink-0"
        >
          <h1 className="text-xl font-bold text-slate-800">
            🛍️ AI Shopping Assistant
          </h1>
        </motion.div>

        {/* Sidebar - Fixed width, full height */}
        <div className="hidden lg:block flex-shrink-0">
          <Sidebar 
            products={products}
            onProductRemove={removeProduct}
            onProductsClear={clearProducts}
          />
        </div>

        {/* Main Chat Interface - Takes remaining space */}
        <div className="flex-1 min-w-0">
          <ChatInterface 
            messages={messages}
            isTyping={isTyping}
            onSendMessage={sendMessage}
          />
        </div>

        {/* Mobile Sidebar - Could be implemented as a drawer/modal */}
        <div className="lg:hidden">
          {/* This could be a collapsible section or modal for mobile */}
        </div>
      </div>
    </div>
  );
}
