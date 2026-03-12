import { motion, useInView } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { useRef } from 'react';
import type { ReactNode } from 'react';

type AnimationType = 'slideInBottom' | 'slideInLeft' | 'slideInRight' | 'fadeIn' | 'scaleIn';

interface ScrollRevealProps {
  children: ReactNode;
  animation?: AnimationType;
  delay?: number;
  duration?: number;
  className?: string;
  once?: boolean;
}

const animations: Record<AnimationType, Variants> = {
  slideInBottom: {
    hidden: { opacity: 0, y: 60 },
    visible: { opacity: 1, y: 0 },
  },
  slideInLeft: {
    hidden: { opacity: 0, x: -60 },
    visible: { opacity: 1, x: 0 },
  },
  slideInRight: {
    hidden: { opacity: 0, x: 60 },
    visible: { opacity: 1, x: 0 },
  },
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  },
  scaleIn: {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { opacity: 1, scale: 1 },
  },
};

export function ScrollReveal({
  children,
  animation = 'slideInBottom',
  delay = 0,
  duration = 0.8,
  className = '',
  once = true,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once, margin: '-100px' });

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={animations[animation]}
      transition={{
        duration,
        delay,
        ease: [0.19, 1, 0.22, 1], // outExpo
      }}
      className={className}
      style={{ willChange: 'transform, opacity' }}
    >
      {children}
    </motion.div>
  );
}
