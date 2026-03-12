'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

// Map skill name → display label + emoji
const SKILL_META: Record<string, { label: string; emoji: string }> = {
    'chat-analyzer': { label: '聊天分析', emoji: '💬' },
    'date-planning': { label: '约会策划', emoji: '📅' },
    'persona-builder': { label: '人设打造', emoji: '🎭' },
    'gift-advisor': { label: '礼物参谋', emoji: '🎁' },
    'parallel-universe': { label: '平行宇宙', emoji: '🔮' },
    'web-search': { label: '全网搜索', emoji: '🔍' },
};

interface SkillCardProps {
    skillNames: string[];
}

export function SkillCard({ skillNames }: SkillCardProps) {
    const [expanded, setExpanded] = useState(false);

    if (!skillNames || skillNames.length === 0) return null;

    const primary = SKILL_META[skillNames[0]] ?? { label: skillNames[0], emoji: '⚡' };
    const extra = skillNames.slice(1);

    return (
        <div className="mb-2">
            <button
                onClick={() => setExpanded(v => !v)}
                className={cn(
                    'flex items-center gap-2 text-xs rounded-lg px-3 py-1.5 transition-all duration-200',
                    'bg-indigo-500/10 border border-indigo-500/25 text-indigo-300',
                    'hover:bg-indigo-500/20',
                )}
            >
                <Sparkles size={12} className="text-indigo-400 shrink-0" />
                <span className="font-medium">
                    {primary.emoji} {primary.label}
                    {extra.length > 0 && ` + ${extra.length} 个技能`}
                </span>
                <span className="ml-auto text-indigo-400/60 text-[10px]">已激活</span>
                {extra.length > 0 && (
                    expanded
                        ? <ChevronDown size={11} className="ml-1 text-indigo-400/60" />
                        : <ChevronRight size={11} className="ml-1 text-indigo-400/60" />
                )}
            </button>

            {/* Extra skills list */}
            {expanded && extra.length > 0 && (
                <div className="mt-1 pl-4 flex flex-col gap-0.5">
                    {extra.map(name => {
                        const meta = SKILL_META[name] ?? { label: name, emoji: '⚡' };
                        return (
                            <span key={name} className="text-[11px] text-indigo-300/60">
                                {meta.emoji} {meta.label}
                            </span>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
