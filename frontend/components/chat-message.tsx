'use client';

import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import { ChatMessage } from '../data/dummy-data';

interface ChatMessageProps {
  message: ChatMessage;
  index: number;
}

// Function to format message content with URLs and line breaks
function formatMessageContent(content: string) {
  // URL regex pattern
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  
  // Split content by URLs and process each part
  const parts = content.split(urlRegex);
  
  return parts.map((part, index) => {
    if (urlRegex.test(part)) {
      // This is a URL - make it clickable and blue
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 underline break-all"
        >
          {part}
        </a>
      );
    } else {
      // This is regular text - add line breaks
      return (
        <span key={index} className="whitespace-pre-wrap">
          {part}
        </span>
      );
    }
  });
}

export function ChatMessageComponent({ message, index }: ChatMessageProps) {
  const isUser = message.role === 'user';
  
  return (
    <motion.div
      initial={{ 
        opacity: 0, 
        x: isUser ? 50 : -50,
        y: 20 
      }}
      animate={{ 
        opacity: 1, 
        x: 0,
        y: 0 
      }}
      transition={{ 
        duration: 0.4, 
        delay: index * 0.1,
        ease: "easeOut"
      }}
      className={`flex items-start space-x-3 mb-6 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: index * 0.1 + 0.2 }}
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-lg ${
          isUser 
            ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
            : 'bg-gradient-to-r from-slate-600 to-slate-700'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </motion.div>
      
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ delay: index * 0.1 + 0.3 }}
        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl backdrop-blur-sm shadow-lg border ${
          isUser
            ? 'bg-gradient-to-r from-blue-500/90 to-blue-600/90 text-white rounded-br-sm border-blue-400/30'
            : 'bg-gradient-to-r from-white/80 to-white/70 text-slate-800 rounded-bl-sm border-white/40'
        }`}
      >
        <div className="text-sm leading-relaxed font-medium">
          {formatMessageContent(message.content)}
        </div>
        <p className={`text-xs mt-2 ${
          isUser ? 'text-blue-100' : 'text-slate-500'
        }`}>
          {message.timestamp.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true
          })}
        </p>
      </motion.div>
    </motion.div>
  );
}
