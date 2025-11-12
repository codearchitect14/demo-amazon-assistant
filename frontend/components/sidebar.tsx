'use client';

import { motion } from 'framer-motion';
import { SearchBar } from './search-bar';
import { ProductCard } from './product-card';
import { Product } from '../lib/api-client';
import { useState, useMemo } from 'react';

interface SidebarProps {
  products: Product[];
  onProductRemove?: (productId: string) => void;
  onProductsClear?: () => void;
}

export function Sidebar({ products, onProductRemove, onProductsClear }: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredProducts = useMemo(() => {
    if (!searchQuery.trim()) return products;
    
    const query = searchQuery.toLowerCase();
    return products.filter(product => 
      product.title.toLowerCase().includes(query) ||
      product.price.toLowerCase().includes(query) ||
      (product.category && product.category.toLowerCase().includes(query))
    );
  }, [products, searchQuery]);

  return (
    <motion.div
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full lg:w-96 xl:w-[420px] bg-white/30 backdrop-blur-xl border-r border-white/30 flex flex-col h-full shadow-2xl"
    >
      {/* Fixed Header Section */}
      <div className="p-6 border-b border-white/20 bg-gradient-to-b from-white/50 to-white/30 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-xl">🛍️</span>
              </div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Product Discovery
              </h2>
            </div>
            {products.length > 0 && onProductsClear && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onProductsClear}
                className="text-xs px-3 py-1 bg-red-100 text-red-600 rounded-full hover:bg-red-200 transition-colors"
              >
                Clear All
              </motion.button>
            )}
          </div>
          
          <SearchBar onSearch={setSearchQuery} />
          
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
              {filteredProducts.length > 0 ? 'Found Products' : 'No Products Yet'}
            </h3>
            {filteredProducts.length > 0 && (
              <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full">
                {filteredProducts.length}
              </span>
            )}
          </div>
        </motion.div>
      </div>
      
      {/* Scrollable Products Section */}
      <div 
        className="flex-1 overflow-y-auto p-6 pt-4"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(148, 163, 184, 0.3) transparent' }}
      >
        {filteredProducts.length > 0 ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {filteredProducts.map((product, index) => (
              <ProductCard 
                key={product.id} 
                product={product} 
                index={index}
                onRemove={onProductRemove}
              />
            ))}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="w-16 h-16 bg-gradient-to-r from-slate-200 to-slate-300 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🔍</span>
            </div>
            <p className="text-slate-500 text-sm">
              {searchQuery ? 'No products match your search' : 'Start chatting to discover products!'}
            </p>
            <p className="text-slate-400 text-xs mt-2">
              Ask the AI assistant about products you're interested in
            </p>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
