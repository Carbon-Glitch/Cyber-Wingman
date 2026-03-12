'use client';

export type ThoughtStep = {
    step: number;
    action: string;
    description: string;
    args?: Record<string, unknown>;
    reasoning?: string;
};

interface ThoughtsPanelProps {
    thoughts: ThoughtStep[] | null;
    currentStep?: string;
}

export function ThoughtsPanel({ thoughts }: ThoughtsPanelProps) {
    if (!thoughts || thoughts.length === 0) {
        return null;
    }

    const nonReasoningSteps = thoughts.filter(t => t.action !== 'reasoning');
    const reasoningStep = thoughts.find(t => t.action === 'reasoning');

    return (
        <div className="mt-1.5 mx-1 rounded-lg border border-neutral-700/50 bg-neutral-900/50 overflow-hidden mb-3">
            {/* Tool call steps */}
            {nonReasoningSteps.length > 0 && (
                <div className="divide-y divide-neutral-800/50">
                    {nonReasoningSteps.map(step => (
                        <div key={step.step} className="px-4 py-2.5 flex items-start gap-3">
                            <div className="w-5 h-5 rounded-full bg-neutral-800 border border-neutral-700 text-[10px] text-neutral-400 flex items-center justify-center font-mono shrink-0 mt-0.5">
                                {step.step}
                            </div>
                            <div className="min-w-0">
                                <div className="text-[12px] text-neutral-200 font-medium">
                                    {step.description}
                                </div>
                                {step.args && Object.keys(step.args).length > 0 && (
                                    <div className="mt-1 text-[11px] text-neutral-500 font-mono truncate">
                                        {JSON.stringify(step.args).slice(0, 80)}
                                        {JSON.stringify(step.args).length > 80 ? '…' : ''}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Reasoning / thinking trace */}
            {reasoningStep?.reasoning && (
                <div className="px-4 py-3 border-t border-neutral-800/50">
                    <div className="text-[11px] text-purple-400/80 font-medium mb-1.5">
                        🧠 内部推理过程
                    </div>
                    <div className="text-[11px] text-neutral-400 font-mono leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {reasoningStep.reasoning}
                    </div>
                </div>
            )}
        </div>
    );
}
