import { motion } from 'framer-motion';
import { PricingCard } from '@/components/PricingCard';
import type { PricingPlan } from '@/types';

const plans: PricingPlan[] = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'month',
    description: 'Get started with basic features',
    features: [
      '10 messages per day',
      'Basic screenshot analysis',
      'Standard reply suggestions',
      'Community support',
    ],
    cta: 'Start Free',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$19',
    period: 'month',
    description: 'Unlock the full experience',
    features: [
      'Unlimited messages',
      'Advanced analysis with red flag detection',
      'Premium reply suggestions',
      'Personality testing',
      'Priority support',
    ],
    popular: true,
    cta: 'Get Pro',
  },
  {
    id: 'elite',
    name: 'Elite',
    price: '$49',
    period: 'month',
    description: 'For serious relationship builders',
    features: [
      'Everything in Pro',
      'Parallel universe simulations',
      'Voice message analysis',
      '1-on-1 strategy sessions',
      'White-glove onboarding',
    ],
    cta: 'Go Elite',
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="relative py-24 lg:py-32">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-cyber-black via-cyber-darker to-cyber-black" />
      
      {/* Glow Effect */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyber-pink/5 rounded-full blur-3xl" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
          className="text-center mb-16 lg:mb-20"
        >
          <p className="font-mono text-xs text-cyber-pink uppercase tracking-[0.3em] mb-4">
            Pricing Plans
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black italic text-white mb-4">
            CHOOSE YOUR <span className="gradient-text">PLAN</span>
          </h2>
          <p className="text-lg text-neutral-03 max-w-2xl mx-auto">
            Start free, upgrade when you're ready
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <PricingCard key={plan.id} plan={plan} index={index} />
          ))}
        </div>

        {/* Trust Badge */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="text-center text-sm text-neutral-03 mt-8"
        >
          No credit card required for free plan • Cancel anytime
        </motion.p>
      </div>
    </section>
  );
}
