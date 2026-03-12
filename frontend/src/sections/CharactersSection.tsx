import { motion } from 'framer-motion';
import { CharacterCard } from '@/components/CharacterCard';
import type { Character } from '@/types';

const characters: Character[] = [
  {
    id: 'aphrodite',
    name: 'APHRODITE',
    title: 'The Savage Bestie',
    tag: 'FOR SINGLE WOMEN',
    color: 'pink',
    traits: ['Hyper-Analytical', 'Zero BS'],
    description: 'Your brutally honest best friend who sees through the games and tells you exactly what he\'s really thinking.',
    image: '/images/aphrodite.png',
  },
  {
    id: 'chiron',
    name: 'CHIRON',
    title: 'The Strategic Mentor',
    tag: 'FOR SINGLE MEN',
    color: 'cyan',
    traits: ['Field-Tested', 'No Fluff'],
    description: 'Your personal dating strategist who breaks down social dynamics and gives you actionable tactics that work.',
    image: '/images/chiron.png',
  },
  {
    id: 'odysseus',
    name: 'ODYSSEUS',
    title: 'The Marriage Architect',
    tag: 'FOR MARRIED MEN',
    color: 'amber',
    traits: ['Rational', 'Long-term'],
    description: 'Your relationship engineer who helps you navigate the complex dynamics of marriage with strategic precision.',
    image: '/images/odysseus.png',
  },
  {
    id: 'persephone',
    name: 'PERSEPHONE',
    title: 'The Power Queen',
    tag: 'FOR MARRIED WOMEN',
    color: 'purple',
    traits: ['Calculated', 'Dominant'],
    description: 'Your inner circle advisor who understands power dynamics and helps you maintain control of your relationship.',
    image: '/images/persephone.png',
  },
];

export function CharactersSection() {
  return (
    <section id="characters" className="relative py-24 lg:py-32">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-cyber-black via-cyber-darker to-cyber-black" />
      
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
            Four AI Personalities
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black italic text-white mb-4">
            CHOOSE YOUR <span className="gradient-text">WINGMAN</span>
          </h2>
          <p className="text-lg text-neutral-03 max-w-2xl mx-auto">
            Four AI personalities tailored to your specific situation and goals
          </p>
        </motion.div>

        {/* Character Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {characters.map((character, index) => (
            <CharacterCard 
              key={character.id} 
              character={character} 
              index={index}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
