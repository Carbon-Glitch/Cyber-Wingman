import { motion } from 'framer-motion';
import type { Feature } from '@/types';
import { Check } from 'lucide-react';

interface FeatureBlockProps {
  feature: Feature;
  index?: number;
  reversed?: boolean;
}

export function FeatureBlock({ feature, reversed = false }: FeatureBlockProps) {
  return (
    <div className={`grid lg:grid-cols-2 gap-12 lg:gap-20 items-center ${reversed ? 'lg:flex-row-reverse' : ''}`}>
      {/* Content */}
      <motion.div
        initial={{ opacity: 0, x: reversed ? 60 : -60 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{
          duration: 0.8,
          ease: [0.19, 1, 0.22, 1],
        }}
        className={reversed ? 'lg:order-2' : ''}
      >
        <h3 className="text-3xl lg:text-4xl font-black italic gradient-text mb-4">
          {feature.title}
        </h3>
        <p className="text-lg text-neutral-02 mb-8 leading-relaxed">
          {feature.description}
        </p>

        {/* Highlights */}
        <ul className="space-y-4">
          {feature.highlights.map((highlight, i) => (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{
                duration: 0.5,
                delay: i * 0.1,
                ease: [0.19, 1, 0.22, 1],
              }}
              className="flex items-center gap-4"
            >
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-cyber-pink/20 flex items-center justify-center">
                <Check className="w-4 h-4 text-cyber-pink" />
              </div>
              <span className="text-neutral-02">{highlight}</span>
            </motion.li>
          ))}
        </ul>
      </motion.div>

      {/* Visual */}
      <motion.div
        initial={{ opacity: 0, x: reversed ? -60 : 60 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{
          duration: 0.8,
          ease: [0.19, 1, 0.22, 1],
        }}
        className={`relative ${reversed ? 'lg:order-1' : ''}`}
      >
        <div className="relative aspect-square max-w-md mx-auto">
          {/* Glow Background */}
          <div className="absolute inset-0 bg-cyber-pink/10 rounded-full blur-3xl" />
          
          {/* Feature Illustration Placeholder */}
          <div className="relative h-full rounded-2xl glass-card border border-cyber-pink/20 overflow-hidden flex items-center justify-center">
            <div className="text-center p-8">
              <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-cyber-pink/30 to-cyber-pink/10 flex items-center justify-center">
                <span className="text-4xl font-black italic text-cyber-pink">
                  {feature.id.padStart(2, '0')}
                </span>
              </div>
              <p className="text-neutral-03 text-sm uppercase tracking-wider">
                {feature.title}
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
