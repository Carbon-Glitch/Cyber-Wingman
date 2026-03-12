'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Brain, Bot, Wrench, Loader2, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Message } from '@/components/chat';

interface Props {
    msg: Message;
    mode: 'fast' | 'wingman' | 'crew';
    children: React.ReactNode;
}

export function CollapsibleThinkingPanel({ msg, mode, children }: Props) {
    const [expanded, setExpanded] = useState(!msg.isDone);

    // 当 props 变化时派生 state（避免 useEffect 造成的级联渲染）
    const [prevIsDone, setPrevIsDone] = useState(msg.isDone);
    if (msg.isDone !== prevIsDone) {
        setPrevIsDone(msg.isDone);
        setExpanded(!msg.isDone);
    }

    // Fast 模式下完全不显示思考过程容器
    if (mode === 'fast') {
        return null;
    }

    // 计算调用了多少资源
    const toolsCount = msg.toolSteps?.length || 0;
    const skillsCount = msg.activatedSkills?.length || 0;
    const thoughtsCount = msg.thoughts?.length || 0;
    const subsCount = msg.subagentSpawned?.length || 0;

    const totalActions = toolsCount + skillsCount + thoughtsCount + subsCount;

    // 没有任何思考痕迹（且不在思考中），不渲染面板
    if (totalActions === 0 && !msg.currentStep && msg.isDone) {
        return null;
    }

    return (
        <div className="mb-4">
            <button
                onClick={() => setExpanded((v) => !v)}
                className="group flex items-center gap-2 text-[13px] font-medium text-neutral-400 hover:text-neutral-200 transition-colors w-fit p-1 rounded-md hover:bg-neutral-800/50"
            >
                {!msg.isDone ? (
                    <>
                        <Loader2 size={14} className="animate-spin text-blue-400 shrink-0" />
                        <span className="text-neutral-300">
                            {msg.currentStep ? (
                                <span className="truncate max-w-[200px]">{msg.currentStep}</span>
                            ) : (
                                "正在思考中..."
                            )}
                        </span>
                    </>
                ) : (
                    <>
                        <CheckCircle2 size={14} className="text-emerald-500/80 shrink-0" />
                        <span className="text-neutral-500 group-hover:text-neutral-300 transition-colors duration-200">
                            已完成思考
                            {toolsCount > 0 && `，调用 ${toolsCount} 个工具`}
                            {skillsCount > 0 && `，激活 ${skillsCount} 个技能`}
                            {subsCount > 0 && `，派发 ${subsCount} 个子代理`}
                        </span>
                    </>
                )}

                <motion.div
                    animate={{ rotate: expanded ? 180 : 0 }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                >
                    <ChevronDown size={14} className="text-neutral-500 ml-1" />
                </motion.div>
            </button>

            <AnimatePresence initial={false}>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0, marginTop: 0 }}
                        animate={{ height: 'auto', opacity: 1, marginTop: 8 }}
                        exit={{ height: 0, opacity: 0, marginTop: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div className="pl-3 border-l-2 border-neutral-700/40 py-1 space-y-3">
                            {children}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
