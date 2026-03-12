import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight } from 'lucide-react';
import { GlowButton } from '@/components/GlowButton';
import Link from 'next/link';
import type { Character } from '@/types';

const characters: Character[] = [
  {
    id: 'aphrodite',
    name: 'APHRODITE',
    title: 'The Savage Bestie',
    tag: 'FOR SINGLE WOMEN',
    color: 'pink',
    traits: ['Hyper-Analytical', 'Zero BS'],
    description: 'Your brutally honest best friend who sees through the games.',
    image: '/images/aphrodite.png',
  },
  {
    id: 'chiron',
    name: 'CHIRON',
    title: 'The Strategic Mentor',
    tag: 'FOR SINGLE MEN',
    color: 'cyan',
    traits: ['Field-Tested', 'No Fluff'],
    description: 'Your personal dating strategist who breaks down social dynamics.',
    image: '/images/chiron.png',
  },
  {
    id: 'odysseus',
    name: 'ODYSSEUS',
    title: 'The Marriage Architect',
    tag: 'FOR MARRIED MEN',
    color: 'amber',
    traits: ['Rational', 'Long-term'],
    description: 'Your relationship engineer for navigating marriage dynamics.',
    image: '/images/odysseus.png',
  },
  {
    id: 'persephone',
    name: 'PERSEPHONE',
    title: 'The Power Queen',
    tag: 'FOR MARRIED WOMEN',
    color: 'purple',
    traits: ['Calculated', 'Dominant'],
    description: 'Your inner circle advisor for relationship power dynamics.',
    image: '/images/persephone.png',
  },
];

const glowClasses = {
  pink: 'character-glow-pink',
  cyan: 'character-glow-cyan',
  amber: 'character-glow-amber',
  purple: 'character-glow-purple',
};

export function Hero() {
  const [activeCharacter, setActiveCharacter] = useState<Character>(characters[0]);

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 grid-bg opacity-50" />
      <div className="absolute inset-0 scanline-effect" />
      
      {/* Gradient Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-pink/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyber-cyan/10 rounded-full blur-3xl" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Content */}
          <div className="text-center lg:text-left">
            {/* Eyebrow */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="font-mono text-xs text-cyber-pink uppercase tracking-[0.3em] mb-6"
            >
              Your AI Relationship Coach
            </motion.p>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-black italic leading-tight mb-6"
            >
              <span className="gradient-text">Decode the Game.</span>
              <br />
              <span className="text-white">Win at Love.</span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="text-lg text-neutral-02 mb-8 max-w-xl mx-auto lg:mx-0"
            >
              Four AI personalities. One mission: to give you the unfair advantage 
              in modern dating and relationships.
            </motion.p>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
            >
              <Link href="/login">
                <GlowButton size="lg">
                  Start Free Trial
                </GlowButton>
              </Link>
              <a 
                href="#features" 
                className="inline-flex items-center justify-center gap-2 text-neutral-02 hover:text-white transition-colors"
              >
                See How It Works
                <ChevronRight className="w-4 h-4" />
              </a>
            </motion.div>
          </div>

          {/* Right: Character Showcase */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="relative"
          >
            {/* Character Image */}
            <div className="relative w-72 h-72 sm:w-80 sm:h-80 lg:w-96 lg:h-96 mx-auto">
              {/* Glow Effect */}
              <div className={`
                absolute inset-0 rounded-full transition-all duration-500
                ${glowClasses[activeCharacter.color as keyof typeof glowClasses]}
              `} />
              
              {/* Image Container */}
              <div className="relative w-full h-full rounded-full overflow-hidden border-2 border-white/10">
                <AnimatePresence mode="wait">
                  <motion.img
                    key={activeCharacter.id}
                    src={activeCharacter.image}
                    alt={activeCharacter.name}
                    initial={{ opacity: 0, scale: 1.1 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.5 }}
                    className="w-full h-full object-cover object-top"
                  />
                </AnimatePresence>
              </div>

              {/* Character Info */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeCharacter.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-center whitespace-nowrap"
                >
                  <p className="text-2xl font-black italic gradient-text">
                    {activeCharacter.name}
                  </p>
                  <p className="text-xs text-neutral-03 uppercase tracking-[0.2em]">
                    {activeCharacter.title}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Character Selector */}
            <div className="flex justify-center gap-3 mt-12">
              {characters.map((char) => (
                <button
                  key={char.id}
                  onClick={() => setActiveCharacter(char)}
                  className={`
                    w-12 h-12 rounded-full overflow-hidden border-2 transition-all duration-300
                    ${activeCharacter.id === char.id 
                      ? `border-cyber-${char.color} scale-110` 
                      : 'border-white/20 opacity-60 hover:opacity-100'
                    }
                  `}
                >
                  <img
                    src={char.image}
                    alt={char.name}
                    className="w-full h-full object-cover object-top"
                  />
                </button>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <div className="w-6 h-10 rounded-full border-2 border-white/20 flex justify-center pt-2">
          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-cyber-pink"
          />
        </div>
      </motion.div>
    </section>
  );
}
