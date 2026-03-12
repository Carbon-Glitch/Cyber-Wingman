'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export type ToolStepStatus = 'running' | 'success' | 'error';

interface ToolStepCardProps {
    toolName: string;
    status: ToolStepStatus;
    args?: Record<string, unknown>;
}

const TOOL_DISPLAY: Record<string, { icon: string; label: string }> = {
    web_search: { icon: '🔍', label: '全网搜索' },
    date_planning_search: { icon: '📅', label: '约会策划搜索' },
    web_fetch: { icon: '🌐', label: '网页抓取' },
    ideal_type_test: { icon: '🧪', label: '理想型测试' },
    emotion_analysis: { icon: '💬', label: '情绪分析' },
    reply_generator: { icon: '✍️', label: '回复生成' },
    knowledge_search: { icon: '📚', label: '知识库检索' },
    load_skill: { icon: '📦', label: '加载技能' },
    compact: { icon: '🗜️', label: '上下文压缩' },
    time_awareness: { icon: '⏳', label: '时间感知推演' },
    data_visualizer: { icon: '📊', label: '关系雷达图表' },
    ask_user: { icon: '🙋', label: '询问核心参数' },
    task_create: { icon: '📝', label: '拆解制定任务' },
    task_update: { icon: '🔄', label: '更新任务进度' },
    task_list: { icon: '📋', label: '检视任务架构' },
    task_get: { icon: '🔍', label: '获取任务节点内容' },
    spawn_subagent: { icon: '🤖', label: '交办子代理执行' },
};

function getToolDisplay(name: string) {
    return TOOL_DISPLAY[name] || { icon: '⚙️', label: name };
}

export function ToolStepCard({ toolName, status, args }: ToolStepCardProps) {
    const [expanded, setExpanded] = useState(false);
    const display = getToolDisplay(toolName);

    return (
        <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-2"
        >
            <button
                onClick={() => args && Object.keys(args).length > 0 && setExpanded(!expanded)}
                className={cn(
                    "flex items-center gap-2.5 w-full text-left px-3 py-2 rounded-xl text-sm transition-all",
                    "border",
                    status === 'running' && "bg-neutral-800/60 border-neutral-700/50 text-neutral-300",
                    status === 'success' && "bg-emerald-950/30 border-emerald-800/30 text-emerald-300",
                    status === 'error' && "bg-red-950/30 border-red-800/30 text-red-300",
                )}
            >
                {/* Status icon */}
                {status === 'running' && (
                    <Loader2 size={15} className="animate-spin text-blue-400 shrink-0" />
                )}
                {status === 'success' && (
                    <CheckCircle2 size={15} className="text-emerald-400 shrink-0" />
                )}
                {status === 'error' && (
                    <XCircle size={15} className="text-red-400 shrink-0" />
                )}

                {/* Tool display name */}
                <span className="shrink-0">{display.icon}</span>
                <span className="font-medium truncate">{display.label}</span>

                {/* Expand chevron */}
                {args && Object.keys(args).length > 0 && (
                    <span className="ml-auto shrink-0">
                        {expanded
                            ? <ChevronUp size={14} className="text-neutral-500" />
                            : <ChevronDown size={14} className="text-neutral-500" />
                        }
                    </span>
                )}
            </button>

            {/* Expanded args */}
            <AnimatePresence>
                {expanded && args && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="ml-8 mt-1 px-3 py-2 text-xs text-neutral-400 bg-neutral-900/50 border border-neutral-800 rounded-lg font-mono overflow-hidden"
                    >
                        {Object.entries(args).map(([key, val]) => (
                            <div key={key} className="flex gap-2">
                                <span className="text-neutral-500">{key}:</span>
                                <span className="text-neutral-300 break-all">{String(val)}</span>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
