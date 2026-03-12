import { motion } from 'framer-motion';
import { useRef } from 'react';
import { Quote } from 'lucide-react';

const testimonials = [
  {
    id: '1',
    quote: "Aphrodite called out his breadcrumbing before I even realized what was happening. Saved me months of wasted time.",
    author: 'Sarah M.',
    character: 'Aphrodite User',
  },
  {
    id: '2',
    quote: "Chiron's advice actually works. My match rate tripled in two weeks. The tactical breakdowns are game-changing.",
    author: 'Jason T.',
    character: 'Chiron User',
  },
  {
    id: '3',
    quote: "Odysseus helped me navigate a potential divorce and save my marriage. His strategic perspective was invaluable.",
    author: 'Michael R.',
    character: 'Odysseus User',
  },
  {
    id: '4',
    quote: "Persephone taught me how to reclaim power in my relationship. Life-changing advice that actually works.",
    author: 'Emily K.',
    character: 'Persephone User',
  },
];

export function Testimonials() {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <section className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-cyber-darker to-cyber-black" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
          className="text-center mb-16"
        >
          <p className="font-mono text-xs text-cyber-pink uppercase tracking-[0.3em] mb-4">
            User Stories
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black italic text-white">
            WHAT USERS <span className="gradient-text">SAY</span>
          </h2>
        </motion.div>

        {/* Testimonials Carousel */}
        <div ref={containerRef} className="relative">
          <motion.div
            initial={{ opacity: 0, x: 60 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
            className="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={testimonial.id}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{
                  duration: 0.6,
                  delay: index * 0.1,
                  ease: [0.19, 1, 0.22, 1],
                }}
                className="flex-shrink-0 w-full sm:w-[400px] snap-start"
              >
                <div className="h-full p-8 rounded-2xl glass-card border border-white/10 hover:border-cyber-pink/30 transition-colors duration-300">
                  {/* Quote Icon */}
                  <Quote className="w-8 h-8 text-cyber-pink/40 mb-4" />
                  
                  {/* Quote */}
                  <p className="text-lg text-neutral-02 mb-6 leading-relaxed">
                    "{testimonial.quote}"
                  </p>
                  
                  {/* Author */}
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyber-pink/30 to-cyber-pink/10 flex items-center justify-center">
                      <span className="text-sm font-bold text-cyber-pink">
                        {testimonial.author.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-white">{testimonial.author}</p>
                      <p className="text-sm text-neutral-03">{testimonial.character}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Scroll Indicators */}
          <div className="flex justify-center gap-2 mt-6">
            {testimonials.map((_, index) => (
              <div
                key={index}
                className="w-2 h-2 rounded-full bg-white/20"
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
