import { motion } from 'framer-motion';
import { FeatureBlock } from '@/components/FeatureBlock';
import type { Feature } from '@/types';

const features: Feature[] = [
  {
    id: '01',
    title: 'Screenshot Analysis',
    description: 'Upload any conversation. Our AI reads between the lines, analyzes emotional subtext, and tells you exactly what\'s really going on.',
    highlights: [
      'Detects breadcrumbing, gaslighting, and mixed signals',
      'Generates 3 tailored response options',
      'Identifies red flags in real-time',
    ],
  },
  {
    id: '02',
    title: 'Perfect Reply Generator',
    description: 'Never stare at your screen wondering what to say. Get three strategically crafted responses for any situation.',
    highlights: [
      'Calibrated to your personality',
      'Adjusts tone based on relationship stage',
      'Learns from your feedback over time',
    ],
  },
  {
    id: '03',
    title: 'Ideal Type Discovery',
    description: '15 rounds of immersive scenarios to uncover what you truly want—and need—in a partner.',
    highlights: [
      'Reveals subconscious attraction patterns',
      'Identifies your non-negotiables',
      'Compares compatibility with current interests',
    ],
  },
  {
    id: '04',
    title: 'What If Simulator',
    description: 'Replay past conversations with different responses. See how small changes could have changed everything.',
    highlights: [
      'Simulates alternative outcomes',
      'Identifies your missed opportunities',
      'Builds pattern recognition for future',
    ],
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="relative py-24 lg:py-32">
      {/* Background */}
      <div className="absolute inset-0 grid-bg opacity-30" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
          className="text-center mb-20 lg:mb-28"
        >
          <p className="font-mono text-xs text-cyber-pink uppercase tracking-[0.3em] mb-4">
            Core Capabilities
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black italic text-white mb-4">
            FEATURES THAT <span className="gradient-text">DELIVER</span>
          </h2>
          <p className="text-lg text-neutral-03 max-w-2xl mx-auto">
            Every tool designed to give you actionable insights and real results
          </p>
        </motion.div>

        {/* Features List */}
        <div className="space-y-24 lg:space-y-32">
          {features.map((feature, index) => (
            <FeatureBlock
              key={feature.id}
              feature={feature}
              index={index}
              reversed={index % 2 === 1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
