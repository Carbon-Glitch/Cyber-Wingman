import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import type { PricingPlan } from '@/types';
import { GlowButton } from './GlowButton';

interface PricingCardProps {
  plan: PricingPlan;
  index: number;
}

export function PricingCard({ plan, index }: PricingCardProps) {
  const isPopular = plan.popular;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true, margin: '-100px' }}
      transition={{
        duration: 0.7,
        delay: index * 0.1,
        ease: [0.19, 1, 0.22, 1],
      }}
      className={`
        relative rounded-2xl p-8
        ${isPopular 
          ? 'bg-gradient-to-b from-cyber-pink/10 to-transparent border-2 border-cyber-pink/50 shadow-glow-pink' 
          : 'bg-white/[0.02] border border-white/10'
        }
      `}
    >
      {/* Popular Badge */}
      {isPopular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="px-4 py-1 bg-cyber-pink text-white text-xs font-bold uppercase tracking-wider rounded-full">
            Most Popular
          </span>
        </div>
      )}

      {/* Plan Name */}
      <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
      <p className="text-sm text-neutral-03 mb-6">{plan.description}</p>

      {/* Price */}
      <div className="mb-8">
        <span className="text-4xl font-black text-white">{plan.price}</span>
        <span className="text-neutral-03">/{plan.period}</span>
      </div>

      {/* Features */}
      <ul className="space-y-4 mb-8">
        {plan.features.map((feature, i) => (
          <li key={i} className="flex items-start gap-3">
            <div className={`
              flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center
              ${isPopular ? 'bg-cyber-pink/20' : 'bg-white/10'}
            `}>
              <Check className={`w-3 h-3 ${isPopular ? 'text-cyber-pink' : 'text-white'}`} />
            </div>
            <span className="text-sm text-neutral-02">{feature}</span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <GlowButton
        variant={isPopular ? 'primary' : 'secondary'}
        color="pink"
        className="w-full justify-center"
      >
        {plan.cta}
      </GlowButton>
    </motion.div>
  );
}
