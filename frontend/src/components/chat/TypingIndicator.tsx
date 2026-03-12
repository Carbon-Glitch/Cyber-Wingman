"use client";

import { motion } from 'framer-motion';

interface TypingIndicatorProps {
  characterColor: string;
  text?: string;
}

export function TypingIndicator({ 
  characterColor, 
  text = "Analyzing..."
}: TypingIndicatorProps) {
  const getColorClass = () => {
    switch (characterColor) {
      case 'cyan': return 'border-cyber-cyan/30 text-cyber-cyan';
      case 'amber': return 'border-cyber-amber/30 text-cyber-amber';
      case 'purple': return 'border-cyber-purple/30 text-cyber-purple';
      default: return 'border-cyber-pink/30 text-cyber-pink';
    }
  };

  const getSpinnerColor = () => {
    switch (characterColor) {
      case 'cyan': return 'border-cyber-cyan';
      case 'amber': return 'border-cyber-amber';
      case 'purple': return 'border-cyber-purple';
      default: return 'border-cyber-pink';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex justify-start pl-14"
    >
      <div className={`
        flex items-center gap-3 
        bg-white/5 border rounded-full 
        px-4 py-2 backdrop-blur-md
        ${getColorClass()}
      `}>
        <span className="text-xs italic">{text}</span>
        <div className="w-4 h-4 relative">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className={`
              w-4 h-4 rounded-full border-2 border-t-transparent
              ${getSpinnerColor()}
            `}
          />
        </div>
      </div>
    </motion.div>
  );
}
