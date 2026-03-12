import { motion } from 'framer-motion';
import type { Character } from '@/types';

interface CharacterCardProps {
  character: Character;
  index: number;
}

const colorClasses = {
  pink: {
    border: 'border-cyber-pink/30 hover:border-cyber-pink/60',
    glow: 'group-hover:shadow-glow-pink',
    tag: 'bg-cyber-pink/20 text-cyber-pink',
    trait: 'border-cyber-pink/30 text-cyber-pink/80',
    gradient: 'from-cyber-pink/20 to-transparent',
  },
  cyan: {
    border: 'border-cyber-cyan/30 hover:border-cyber-cyan/60',
    glow: 'group-hover:shadow-glow-cyan',
    tag: 'bg-cyber-cyan/20 text-cyber-cyan',
    trait: 'border-cyber-cyan/30 text-cyber-cyan/80',
    gradient: 'from-cyber-cyan/20 to-transparent',
  },
  amber: {
    border: 'border-cyber-amber/30 hover:border-cyber-amber/60',
    glow: 'group-hover:shadow-glow-amber',
    tag: 'bg-cyber-amber/20 text-cyber-amber',
    trait: 'border-cyber-amber/30 text-cyber-amber/80',
    gradient: 'from-cyber-amber/20 to-transparent',
  },
  purple: {
    border: 'border-cyber-purple/30 hover:border-cyber-purple/60',
    glow: 'group-hover:shadow-glow-purple',
    tag: 'bg-cyber-purple/20 text-cyber-purple',
    trait: 'border-cyber-purple/30 text-cyber-purple/80',
    gradient: 'from-cyber-purple/20 to-transparent',
  },
};

const gradientTextClasses = {
  pink: 'gradient-text',
  cyan: 'gradient-text-cyan',
  amber: 'gradient-text-amber',
  purple: 'gradient-text-purple',
};

export function CharacterCard({ character, index }: CharacterCardProps) {
  const colors = colorClasses[character.color];
  const gradientText = gradientTextClasses[character.color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 60 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-100px' }}
      transition={{
        duration: 0.8,
        delay: index * 0.15,
        ease: [0.19, 1, 0.22, 1],
      }}
      className={`
        group relative overflow-hidden rounded-2xl
        bg-white/[0.02] border ${colors.border}
        transition-all duration-500
        ${colors.glow}
      `}
    >
      {/* Image Container */}
      <div className="relative h-64 overflow-hidden">
        <motion.img
          src={character.image}
          alt={character.name}
          className="w-full h-full object-cover object-top"
          whileHover={{ scale: 1.1 }}
          transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
        />
        {/* Gradient Overlay */}
        <div className={`absolute inset-0 bg-gradient-to-t ${colors.gradient} to-transparent`} />
        
        {/* Tag */}
        <div className={`absolute top-4 left-4 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${colors.tag}`}>
          {character.tag}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Name & Title */}
        <h3 className={`text-2xl font-black italic mb-1 ${gradientText}`}>
          {character.name}
        </h3>
        <p className="text-sm text-neutral-03 uppercase tracking-[0.2em] mb-4">
          {character.title}
        </p>

        {/* Traits */}
        <div className="flex flex-wrap gap-2 mb-4">
          {character.traits.map((trait, i) => (
            <span
              key={i}
              className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${colors.trait}`}
            >
              {trait}
            </span>
          ))}
        </div>

        {/* Description */}
        <p className="text-sm text-neutral-02 leading-relaxed">
          {character.description}
        </p>
      </div>
    </motion.div>
  );
}
