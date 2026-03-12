'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface StreamingTextProps {
    /** The complete text to render (grows as SSE chunks arrive). */
    text: string;
    /** ms per character for the typewriter effect */
    speed?: number;
    /** Show blinking cursor while typing */
    showCursor?: boolean;
    /**
     * When true, skip the typewriter and render the full text immediately.
     * Set to true once the stream is done (isDone=true) so we don't replay
     * the entire typewriter on every re-render after completion.
     */
    instant?: boolean;
}

export function StreamingText({
    text,
    speed = 15,
    showCursor = true,
    instant = false,
}: StreamingTextProps) {
    // How many characters to show right now
    const [displayedLen, setDisplayedLen] = useState(instant ? text.length : 0);
    // Track the text we've already typed so we only animate *new* characters
    const prevLen = useRef(instant ? text.length : 0);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        // If instant flag is set, jump straight to the end
        if (instant) {
            if (timerRef.current) clearInterval(timerRef.current);
            setDisplayedLen(text.length);
            prevLen.current = text.length;
            return;
        }

        const start = prevLen.current;
        if (start >= text.length) {
            // Nothing new to type
            return;
        }

        // Clear any previous timer before starting a new one
        if (timerRef.current) clearInterval(timerRef.current);

        let current = start;

        timerRef.current = setInterval(() => {
            // Speed up for long text: type multiple chars per tick
            const charsPerTick = Math.max(1, Math.ceil((text.length - current) / 80));
            current = Math.min(current + charsPerTick, text.length);
            setDisplayedLen(current);
            prevLen.current = current;

            if (current >= text.length) {
                if (timerRef.current) clearInterval(timerRef.current);
            }
        }, speed);

        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
        // We intentionally only depend on text.length and instant;
        // prevLen.current tracks internal state without causing re-runs.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [text.length, instant, speed]);

    const visibleText = text.slice(0, displayedLen);
    const isTyping = displayedLen < text.length;

    return (
        <div className="streaming-text-container">
            <div
                className="prose prose-invert prose-sm max-w-none
                    prose-p:my-1.5 prose-li:my-0.5
                    prose-headings:text-neutral-100 prose-headings:font-bold
                    prose-strong:text-neutral-100
                    prose-code:text-indigo-300 prose-code:bg-neutral-800/80 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-xs prose-code:font-mono
                    prose-pre:bg-neutral-900 prose-pre:border prose-pre:border-neutral-700/50 prose-pre:rounded-xl
                    prose-blockquote:border-l-indigo-500/50 prose-blockquote:text-neutral-400
                    prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                "
            >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {visibleText}
                </ReactMarkdown>
            </div>

            {/* Blinking cursor while typing */}
            {showCursor && isTyping && (
                <span className="inline-block w-0.5 h-4 bg-blue-400 ml-0.5 animate-pulse align-text-bottom" />
            )}
        </div>
    );
}
