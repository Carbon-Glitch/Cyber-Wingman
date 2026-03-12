import { motion, useInView } from 'framer-motion';
import { useRef, useEffect, useState } from 'react';
import { UserPlus, MessageSquare, Target } from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'Choose Your Wingman',
    description: 'Select the AI personality that matches your situation and goals.',
    icon: UserPlus,
  },
  {
    number: '02',
    title: 'Share Your Context',
    description: 'Upload screenshots, describe scenarios, or just start chatting.',
    icon: MessageSquare,
  },
  {
    number: '03',
    title: 'Get Your Strategy',
    description: 'Receive actionable advice tailored to your specific situation.',
    icon: Target,
  },
];

function AnimatedNumber({ value, inView }: { value: string; inView: boolean }) {
  const [displayValue, setDisplayValue] = useState(0);
  const numValue = parseInt(value);

  useEffect(() => {
    if (inView) {
      let start = 0;
      const duration = 1000;
      const increment = numValue / (duration / 16);
      
      const timer = setInterval(() => {
        start += increment;
        if (start >= numValue) {
          setDisplayValue(numValue);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.floor(start));
        }
      }, 16);

      return () => clearInterval(timer);
    }
  }, [inView, numValue]);

  return <span>{displayValue.toString().padStart(2, '0')}</span>;
}

export function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="relative py-24 lg:py-32">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-cyber-black to-cyber-darker" />
      
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
            Simple Process
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black italic text-white mb-4">
            HOW IT <span className="gradient-text">WORKS</span>
          </h2>
          <p className="text-lg text-neutral-03 max-w-2xl mx-auto">
            Get started in under 60 seconds
          </p>
        </motion.div>

        {/* Steps */}
        <div ref={ref} className="relative">
          {/* Connecting Line (Desktop) */}
          <div className="hidden lg:block absolute top-24 left-[calc(16.67%+2rem)] right-[calc(16.67%+2rem)] h-px">
            <motion.div
              initial={{ scaleX: 0 }}
              animate={isInView ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 1.5, delay: 0.5, ease: [0.19, 1, 0.22, 1] }}
              className="h-full bg-gradient-to-r from-cyber-pink/50 via-cyber-cyan/50 to-cyber-purple/50 origin-left"
            />
          </div>

          <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, y: 60 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-100px' }}
                  transition={{
                    duration: 0.8,
                    delay: index * 0.2,
                    ease: [0.19, 1, 0.22, 1],
                  }}
                  className="relative text-center"
                >
                  {/* Step Number */}
                  <div className="relative inline-flex items-center justify-center w-20 h-20 mb-6">
                    <div className="absolute inset-0 rounded-full bg-cyber-pink/10" />
                    <div className="absolute inset-2 rounded-full bg-cyber-pink/20" />
                    <span className="relative text-3xl font-black italic gradient-text">
                      <AnimatedNumber value={step.number} inView={isInView} />
                    </span>
                  </div>

                  {/* Icon */}
                  <div className="inline-flex items-center justify-center w-12 h-12 mb-4 rounded-xl bg-white/5 border border-white/10">
                    <Icon className="w-5 h-5 text-cyber-pink" />
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-bold text-white mb-3">
                    {step.title}
                  </h3>
                  <p className="text-neutral-03">
                    {step.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
