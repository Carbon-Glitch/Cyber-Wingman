import { motion } from 'framer-motion';
import { GlowButton } from '@/components/GlowButton';
import Link from 'next/link';

export function CTASection() {
  return (
    <section className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-cyber-darker to-cyber-black" />
      
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px]">
        <div className="absolute inset-0 bg-gradient-to-r from-cyber-pink/20 via-cyber-cyan/10 to-cyber-purple/20 blur-3xl" />
      </div>
      
      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
        >
          {/* Headline */}
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black italic text-white mb-6">
            Ready to Stop Playing{' '}
            <span className="gradient-text">Games?</span>
          </h2>
          
          {/* Subheadline */}
          <p className="text-lg text-neutral-02 mb-10 max-w-2xl mx-auto">
            Join thousands who've already decoded the rules of modern dating. 
            Your AI wingman is waiting.
          </p>
          
          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <Link href="/chat">
              <GlowButton size="lg" className="animate-pulse-glow">
                Start Your Free Trial
              </GlowButton>
            </Link>
          </motion.div>
          
          {/* Trust Badge */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="text-sm text-neutral-03 mt-6"
          >
            No credit card required • Cancel anytime
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}
