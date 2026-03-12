'use client';

import { motion } from 'framer-motion';
import { Brain, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface ThinkingIndicatorProps {
    content?: string;
    isActive?: boolean;
}

export function ThinkingIndicator({ content, isActive = true }: ThinkingIndicatorProps) {
    const [expanded, setExpanded] = useState(false);

    return (
        <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-3"
        >
            <button
                onClick={() => content && setExpanded(!expanded)}
                className="flex items-center gap-2 text-sm group w-full text-left"
            >
                {/* Pulsing icon */}
                <div className="relative flex items-center justify-center w-5 h-5">
                    {isActive && (
                        <span className="absolute inset-0 rounded-full bg-purple-500/30 animate-ping" />
                    )}
                    <Brain size={14} className="relative text-purple-400" />
                </div>

                <span className="text-purple-300/80 font-medium">
                    {isActive ? '思考中...' : '思考完成'}
                </span>

                {/* Animated gradient bar */}
                {isActive && (
                    <div className="flex-1 h-0.5 rounded-full overflow-hidden bg-neutral-800 ml-2">
                        <motion.div
                            className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-500"
                            animate={{ x: ['-100%', '100%'] }}
                            transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
                            style={{ width: '50%' }}
                        />
                    </div>
                )}

                {content && (
                    expanded
                        ? <ChevronUp size={14} className="text-neutral-500" />
                        : <ChevronDown size={14} className="text-neutral-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
            </button>

            {/* Expandable reasoning content */}
            {expanded && content && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 ml-7 px-3 py-2 text-xs text-neutral-400 bg-neutral-900/50 border border-neutral-800 rounded-lg font-mono leading-relaxed max-h-40 overflow-y-auto"
                >
                    {content}
                </motion.div>
            )}
        </motion.div>
    );
}
