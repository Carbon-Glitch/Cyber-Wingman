"use client";

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Copy, Check } from 'lucide-react';

interface ReplyOptionsCardProps {
    options: string[];
    analysis?: string;
}

const OPTION_STYLES = [
    {
        emoji: '🟢',
        label: '稳妥',
        borderColor: 'border-emerald-500/30',
        hoverBorder: 'hover:border-emerald-400/60',
        bg: 'bg-emerald-500/5',
        hoverBg: 'hover:bg-emerald-500/15',
        glow: 'hover:shadow-[0_0_14px_rgba(16,185,129,0.18)]',
        copiedBorder: 'border-emerald-400',
        copiedBg: 'bg-emerald-500/15',
        copiedText: 'text-emerald-300',
    },
    {
        emoji: '🔵',
        label: '进攻',
        borderColor: 'border-blue-500/30',
        hoverBorder: 'hover:border-blue-400/60',
        bg: 'bg-blue-500/5',
        hoverBg: 'hover:bg-blue-500/15',
        glow: 'hover:shadow-[0_0_14px_rgba(59,130,246,0.18)]',
        copiedBorder: 'border-blue-400',
        copiedBg: 'bg-blue-500/15',
        copiedText: 'text-blue-300',
    },
    {
        emoji: '🟣',
        label: '战略',
        borderColor: 'border-purple-500/30',
        hoverBorder: 'hover:border-purple-400/60',
        bg: 'bg-purple-500/5',
        hoverBg: 'hover:bg-purple-500/15',
        glow: 'hover:shadow-[0_0_14px_rgba(168,85,247,0.18)]',
        copiedBorder: 'border-purple-400',
        copiedBg: 'bg-purple-500/15',
        copiedText: 'text-purple-300',
    },
];

export function ReplyOptionsCard({ options, analysis }: ReplyOptionsCardProps) {
    const [copied, setCopied] = useState<number | null>(null);

    const handleCopy = (text: string, index: number) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopied(index);
            setTimeout(() => setCopied(null), 2000);
        });
    };

    if (!options || options.length === 0) return null;

    return (
        <div className="mt-3 space-y-2">
            {analysis && (
                <p className="text-xs text-neutral-500 flex items-center gap-1.5 ml-0.5">
                    <span className="text-neutral-600">💬</span>
                    <span>{analysis}</span>
                </p>
            )}
            <p className="text-xs font-medium text-neutral-500 ml-0.5">一键复制回复 ↓</p>
            {options.slice(0, 3).map((opt, i) => {
                const style = OPTION_STYLES[i];
                const isCopied = copied === i;
                return (
                    <button
                        key={i}
                        onClick={() => handleCopy(opt, i)}
                        className={cn(
                            'group w-full flex items-start gap-3 rounded-xl border px-4 py-3 text-left text-sm transition-all duration-200',
                            isCopied
                                ? `${style.copiedBorder} ${style.copiedBg}`
                                : `${style.borderColor} ${style.bg} ${style.hoverBorder} ${style.hoverBg} ${style.glow}`
                        )}
                    >
                        <span className="mt-0.5 shrink-0 text-base">{style.emoji}</span>
                        <div className="flex-1 min-w-0">
                            <span className={cn(
                                'block text-xs mb-0.5',
                                isCopied ? style.copiedText : 'text-neutral-500'
                            )}>
                                {style.label}
                            </span>
                            <span className={cn(
                                'block leading-snug',
                                isCopied ? style.copiedText : 'text-neutral-200'
                            )}>
                                {isCopied ? '✅ 已复制到剪贴板！' : `"${opt}"`}
                            </span>
                        </div>
                        <span className={cn(
                            'shrink-0 mt-1 transition-opacity',
                            isCopied ? 'opacity-0' : 'opacity-0 group-hover:opacity-50'
                        )}>
                            {isCopied ? <Check size={14} /> : <Copy size={14} />}
                        </span>
                    </button>
                );
            })}
        </div>
    );
}
