import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface GlowButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary';
  color?: 'pink' | 'cyan' | 'amber' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
}

const colorMap = {
  pink: {
    gradient: 'from-[#ff007a] to-[#ff00a0]',
    glow: 'shadow-[0_0_20px_rgba(255,0,122,0.4)] hover:shadow-[0_0_30px_rgba(255,0,122,0.6)]',
    border: 'border-[#ff007a]/50',
  },
  cyan: {
    gradient: 'from-[#00f0ff] to-[#00a0ff]',
    glow: 'shadow-[0_0_20px_rgba(0,240,255,0.4)] hover:shadow-[0_0_30px_rgba(0,240,255,0.6)]',
    border: 'border-[#00f0ff]/50',
  },
  amber: {
    gradient: 'from-[#ffaa00] to-[#ff7700]',
    glow: 'shadow-[0_0_20px_rgba(255,170,0,0.4)] hover:shadow-[0_0_30px_rgba(255,170,0,0.6)]',
    border: 'border-[#ffaa00]/50',
  },
  purple: {
    gradient: 'from-[#b829dd] to-[#7729dd]',
    glow: 'shadow-[0_0_20px_rgba(184,41,221,0.4)] hover:shadow-[0_0_30px_rgba(184,41,221,0.6)]',
    border: 'border-[#b829dd]/50',
  },
};

const sizeMap = {
  sm: 'px-5 py-2 text-xs',
  md: 'px-7 py-3 text-sm',
  lg: 'px-8 py-4 text-base',
};

export function GlowButton({
  children,
  variant = 'primary',
  color = 'pink',
  size = 'md',
  className = '',
  onClick,
}: GlowButtonProps) {
  const colors = colorMap[color];

  if (variant === 'primary') {
    return (
      <motion.button
        onClick={onClick}
        className={`
          relative overflow-hidden rounded-full font-bold uppercase tracking-[0.1em]
          bg-gradient-to-r ${colors.gradient} text-white
          ${colors.glow}
          ${sizeMap[size]}
          transition-all duration-300
          ${className}
        `}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {children}
      </motion.button>
    );
  }

  return (
    <motion.button
      onClick={onClick}
      className={`
        relative overflow-hidden rounded-full font-medium
        bg-transparent border ${colors.border} text-white
        hover:bg-white/5
        ${sizeMap[size]}
        transition-all duration-300
        ${className}
      `}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {children}
    </motion.button>
  );
}
