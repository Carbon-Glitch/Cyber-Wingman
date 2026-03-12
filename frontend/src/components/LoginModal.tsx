"use client";

import { useState } from 'react';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';

interface LoginModalProps {
    isOpen: boolean;
    onClose?: () => void;
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
    const [email, setEmail] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [sent, setSent] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen) return null;

    const supabase = createSupabaseBrowserClient();

    const handleGoogleLogin = async () => {
        await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
            },
        });
    };

    const handleGithubLogin = async () => {
        await supabase.auth.signInWithOAuth({
            provider: 'github',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
            },
        });
    };

    const handleMagicLink = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email.trim()) return;
        setIsSending(true);
        setError('');
        try {
            const { error } = await supabase.auth.signInWithOtp({
                email,
                options: {
                    emailRedirectTo: `${window.location.origin}/auth/callback`,
                },
            });
            if (error) throw error;
            setSent(true);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to send. Please try again.');
        } finally {
            setIsSending(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal Card */}
            <div className="relative z-10 w-full max-w-sm mx-4 rounded-2xl border border-purple-500/30 bg-gray-950/95 p-8 shadow-[0_0_60px_rgba(168,85,247,0.15)] backdrop-blur-xl">
                {/* Glow top border */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-3/4 bg-gradient-to-r from-transparent via-purple-500 to-transparent" />

                {/* Logo + Title */}
                <div className="flex flex-col items-center mb-6 gap-3">
                    <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-purple-500/40 bg-purple-500/10">
                        <span className="text-3xl">🤖</span>
                        <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-cyan-400 animate-pulse" />
                    </div>
                    <div className="text-center">
                        <h2 className="text-xl font-bold text-white">Login to Continue</h2>
                        <p className="text-sm text-gray-400 mt-1">Login to save your chat history and unlock features</p>
                    </div>
                </div>

                {/* OAuth Buttons */}
                <div className="space-y-3 mb-4">
                    <button
                        onClick={handleGoogleLogin}
                        className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-sm font-medium text-gray-200 transition hover:border-purple-500/50 hover:bg-gray-800"
                    >
                        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        Continue with Google
                    </button>
                    <button
                        onClick={handleGithubLogin}
                        className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-sm font-medium text-gray-200 transition hover:border-purple-500/50 hover:bg-gray-800"
                    >
                        <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
                            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
                        </svg>
                        Continue with GitHub
                    </button>
                </div>

                {/* Divider */}
                <div className="flex items-center gap-3 mb-4">
                    <div className="flex-1 h-px bg-gray-800" />
                    <span className="text-xs text-gray-500">OR</span>
                    <div className="flex-1 h-px bg-gray-800" />
                </div>

                {/* Email Magic Link */}
                {!sent ? (
                    <form onSubmit={handleMagicLink} className="space-y-3">
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your@email.com"
                            required
                            className="w-full rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 transition"
                        />
                        {error && <p className="text-xs text-red-400">{error}</p>}
                        <button
                            type="submit"
                            disabled={isSending}
                            className="w-full rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
                        >
                            {isSending ? 'Sending...' : 'Send Magic Link'}
                        </button>
                    </form>
                ) : (
                    <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 text-center">
                        <p className="text-sm text-green-400">✅ Email sent! Please check your inbox for the login link.</p>
                    </div>
                )}

                {/* Footer */}
                <p className="mt-5 text-center text-xs text-gray-600">
                    By continuing, you agree to our Terms of Service and Privacy Policy.
                </p>
            </div>
        </div>
    );
}
