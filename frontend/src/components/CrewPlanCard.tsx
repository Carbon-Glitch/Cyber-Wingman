"use client";

import { motion } from 'framer-motion';
import { CheckCircle2, Loader2, Clock, Users } from 'lucide-react';

export type CrewTask = {
    id: number;
    subject: string;
    status: 'pending' | 'running' | 'done' | 'error';
};

type CrewPhase = 'plan' | 'dispatch' | 'synthesize' | 'done';

type Props = {
    tasks: CrewTask[];
    phase: CrewPhase;
    planSummary?: string;
};

const phaseLabels: Record<CrewPhase, { label: string; icon: React.ReactNode }> = {
    plan: { label: '规划中', icon: <Clock size={14} className="text-amber-400" /> },
    dispatch: { label: '执行中', icon: <Loader2 size={14} className="animate-spin text-blue-400" /> },
    synthesize: { label: '汇总中', icon: <Loader2 size={14} className="animate-spin text-purple-400" /> },
    done: { label: '完成', icon: <CheckCircle2 size={14} className="text-emerald-400" /> },
};

function statusIcon(status: CrewTask['status']) {
    switch (status) {
        case 'pending': return <Clock size={13} className="text-neutral-500" />;
        case 'running': return <Loader2 size={13} className="animate-spin text-blue-400" />;
        case 'done': return <CheckCircle2 size={13} className="text-emerald-400" />;
        case 'error': return <span className="text-red-400 text-xs">✗</span>;
    }
}

export function CrewPlanCard({ tasks, phase, planSummary }: Props) {
    const doneCount = tasks.filter(t => t.status === 'done').length;
    const progress = tasks.length > 0 ? Math.round((doneCount / tasks.length) * 100) : 0;
    const phaseInfo = phaseLabels[phase] || phaseLabels.plan;

    return (
        <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 backdrop-blur-sm p-3.5 mb-3 space-y-3"
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Users size={15} className="text-indigo-400" />
                    <span className="text-xs font-semibold text-indigo-300">Crew 协作模式</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-neutral-400">
                    {phaseInfo.icon}
                    <span>{phaseInfo.label}</span>
                </div>
            </div>

            {/* Plan summary */}
            {planSummary && (
                <p className="text-xs text-neutral-400 leading-relaxed border-l-2 border-indigo-500/30 pl-2.5">
                    {planSummary.slice(0, 200)}
                </p>
            )}

            {/* Task list */}
            {tasks.length > 0 && (
                <div className="space-y-1.5">
                    {tasks.map((task) => (
                        <div
                            key={task.id}
                            className="flex items-center gap-2 text-xs py-1 px-2 rounded-lg bg-neutral-800/40"
                        >
                            {statusIcon(task.status)}
                            <span className="text-neutral-300 flex-1 truncate">#{task.id} {task.subject}</span>
                            <span className="text-[10px] text-neutral-600 shrink-0">
                                {task.status === 'done' ? '✅' : task.status === 'running' ? '⏳' : '⏸'}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {/* Progress bar */}
            {tasks.length > 0 && (
                <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-neutral-500">
                        <span>{doneCount}/{tasks.length} 已完成</span>
                        <span>{progress}%</span>
                    </div>
                    <div className="h-1 rounded-full bg-neutral-800 overflow-hidden">
                        <motion.div
                            className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                        />
                    </div>
                </div>
            )}
        </motion.div>
    );
}
