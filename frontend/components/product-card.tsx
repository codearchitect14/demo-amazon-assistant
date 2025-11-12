'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { X } from 'lucide-react';
import { Product } from '../lib/api-client';

interface ProductCardProps {
  product: Product;
  index: number;
  onRemove?: (productId: string) => void;
}

export function ProductCard({ product, index, onRemove }: ProductCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      whileHover={{ 
        y: -6, 
        boxShadow: '0 20px 40px rgba(0,0,0,0.15)' 
      }}
      className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-white/30 hover:border-white/50 transition-all duration-300 cursor-pointer group shadow-lg relative"
    >
      {onRemove && (
        <motion.button
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 1 }}
          onClick={(e) => {
            e.stopPropagation();
            onRemove(product.id);
          }}
          className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
        >
          <X className="w-3 h-3" />
        </motion.button>
      )}
      
      <div className="relative overflow-hidden rounded-lg mb-4">
        <Image
          src={product.image || "/placeholder.svg?height=150&width=150&text=No+Image"}
          alt={product.title}
          width={160}
          height={160}
          className="w-full h-32 object-cover group-hover:scale-110 transition-transform duration-300"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = "/placeholder.svg?height=150&width=150&text=No+Image";
          }}
        />
      </div>
      
      <h3 className="font-semibold text-sm text-slate-800 mb-2 line-clamp-2 leading-tight">
        {product.title}
      </h3>
      
      <p className="text-xl font-bold text-slate-900 mb-2">
        {product.price}
      </p>
      
      {product.category && (
        <span className="text-xs text-slate-600 bg-slate-100/80 px-3 py-1 rounded-full inline-block">
          {product.category}
        </span>
      )}
    </motion.div>
  );
}
