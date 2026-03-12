'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Cpu } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SubagentData {
    id: string;
    task: string;
}

interface SubagentCardProps {
    subagents: SubagentData[];
}

export function SubagentCard({ subagents }: SubagentCardProps) {
    const [expanded, setExpanded] = useState(false);

    if (!subagents || subagents.length === 0) return null;

    const primary = subagents[subagents.length - 1]; // Show most recent
    const previous = subagents.slice(0, subagents.length - 1);

    return (
        <div className="mb-2">
            <button
                onClick={() => setExpanded(v => !v)}
                className={cn(
                    'flex items-center gap-2 text-xs rounded-lg px-3 py-1.5 transition-all duration-200 w-full text-left',
                    'bg-amber-500/10 border border-amber-500/25 text-amber-300',
                    'hover:bg-amber-500/20',
                )}
            >
                <Cpu size={14} className="text-amber-400 shrink-0" />
                <div className="flex-1 truncate font-medium">
                    子代理执行: {primary.task}
                    {previous.length > 0 && ` (+${previous.length} 历史)`}
                </div>
                <span className="ml-2 text-amber-400/60 text-[10px] shrink-0 font-mono">
                    [{primary.id}]
                </span>
                {previous.length > 0 && (
                    expanded
                        ? <ChevronDown size={12} className="ml-1 text-amber-400/60 shrink-0" />
                        : <ChevronRight size={12} className="ml-1 text-amber-400/60 shrink-0" />
                )}
            </button>

            {/* Extra subagents list */}
            {expanded && previous.length > 0 && (
                <div className="mt-1 pl-4 flex flex-col gap-1">
                    {previous.map(agent => (
                        <div key={agent.id} className="text-[11px] text-amber-300/60 flex items-center gap-2">
                            <Cpu size={10} />
                            <span className="truncate flex-1">{agent.task}</span>
                            <span className="font-mono opacity-50">[{agent.id}]</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
