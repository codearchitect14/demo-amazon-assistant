'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export function SearchBar({ onSearch }: SearchBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      onSearch(searchTerm);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, onSearch]);

  const clearSearch = () => {
    setSearchTerm('');
  };

  return (
    <div className="relative mb-6">
      <motion.div
        animate={{
          boxShadow: isFocused 
            ? '0 0 0 3px rgba(139, 92, 246, 0.15), 0 10px 25px rgba(0, 0, 0, 0.1)' 
            : '0 0 0 0px rgba(139, 92, 246, 0.15), 0 5px 15px rgba(0, 0, 0, 0.08)',
          scale: isFocused ? 1.02 : 1
        }}
        transition={{ duration: 0.2 }}
        className="relative"
      >
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4 z-10" />
        <motion.input
          type="text"
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className="w-full pl-10 pr-10 py-3 bg-white/80 backdrop-blur-sm border-2 border-white/30 rounded-xl focus:outline-none focus:border-purple-400/60 transition-all duration-300 text-slate-700 placeholder-slate-400 font-medium shadow-lg"
        />
        <motion.div
          animate={{
            opacity: isFocused ? 1 : 0,
            scale: isFocused ? 1 : 0.8
          }}
          className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-400/20 to-pink-400/20 -z-10 blur-xl"
        />
        <AnimatePresence>
          {searchTerm && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={clearSearch}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors z-10"
            >
              <X className="w-4 h-4" />
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
