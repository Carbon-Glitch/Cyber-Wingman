'use client';

import { useState, type FormEvent } from 'react';
import { Zap, Mail, Github, Chrome, Loader2, Bot } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { signInWithEmail, signInWithOAuth } from '../auth-actions';

export default function LoginPage() {
    const [pending, setPending] = useState(false);
    const [emailSent, setEmailSent] = useState(false);
    const [emailFormOpen, setEmailFormOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleOAuth(provider: 'google' | 'github') {
        setPending(true);
        setError(null);
        const result = await signInWithOAuth(provider);
        if (result?.error) {
            setError('Authentication failed. Please try again.');
            setPending(false);
        }
    }

    async function handleEmailSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setPending(true);
        setError(null);
        const form = e.target as HTMLFormElement;
        const email = (form['email'] as HTMLInputElement).value;
        const result = await signInWithEmail(email);
        if (result?.error) {
            setError('Failed to send magic link. Please try again.');
        } else {
            setEmailSent(true);
        }
        setPending(false);
    }

    return (
        <main className="relative min-h-screen flex items-center justify-center bg-black overflow-hidden">
            {/* --- Animated grid background --- */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:60px_60px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,black_40%,transparent_100%)]" />

            {/* --- Glow blobs --- */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-violet-600/10 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-cyan-600/8 blur-[120px] pointer-events-none" />

            {/* --- Card --- */}
            <div className="relative z-10 w-full max-w-sm mx-4 p-8 rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl shadow-2xl shadow-black/60">

                {/* Logo + Title */}
                <div className="flex flex-col items-center gap-3 mb-8">
                    <div className="relative">
                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/30">
                            <Bot size={28} className="text-white" />
                        </div>
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-cyan-400 rounded-full flex items-center justify-center">
                            <Zap size={9} className="text-black" />
                        </div>
                    </div>
                    <div className="text-center">
                        <h1 className="text-lg font-bold text-white tracking-tight">Cyber Wingman</h1>
                        <p className="text-xs text-white/40 mt-0.5">Your AI-powered dating strategist</p>
                    </div>
                </div>

                {/* Success state */}
                {emailSent ? (
                    <div className="text-center py-4">
                        <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-cyan-500/10 flex items-center justify-center">
                            <Mail size={20} className="text-cyan-400" />
                        </div>
                        <p className="text-sm font-medium text-white">Check your inbox</p>
                        <p className="text-xs text-white/40 mt-1">We sent you a magic link to sign in</p>
                        <button
                            onClick={() => setEmailSent(false)}
                            className="mt-4 text-xs text-violet-400 hover:text-violet-300 transition-colors"
                        >
                            Try again
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {/* Google */}
                        <button
                            onClick={() => handleOAuth('google')}
                            disabled={pending}
                            className="flex items-center justify-center gap-2.5 w-full py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-medium text-white/80 hover:bg-white/10 hover:border-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {pending ? <Loader2 size={16} className="animate-spin" /> : <Chrome size={16} />}
                            Continue with Google
                        </button>

                        {/* GitHub */}
                        <button
                            onClick={() => handleOAuth('github')}
                            disabled={pending}
                            className="flex items-center justify-center gap-2.5 w-full py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-medium text-white/80 hover:bg-white/10 hover:border-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {pending ? <Loader2 size={16} className="animate-spin" /> : <Github size={16} />}
                            Continue with GitHub
                        </button>

                        {/* Divider */}
                        <div className="flex items-center gap-2 my-1">
                            <div className="flex-1 h-px bg-white/10" />
                            <span className="text-[10px] text-white/30 uppercase tracking-widest">or</span>
                            <div className="flex-1 h-px bg-white/10" />
                        </div>

                        {/* Email */}
                        {!emailFormOpen ? (
                            <button
                                onClick={() => setEmailFormOpen(true)}
                                disabled={pending}
                                className="flex items-center justify-center gap-2.5 w-full py-3 rounded-xl bg-violet-500/10 border border-violet-500/20 text-sm font-medium text-violet-300 hover:bg-violet-500/20 hover:border-violet-500/30 transition-all disabled:opacity-50"
                            >
                                <Mail size={16} />
                                Continue with Email
                            </button>
                        ) : (
                            <form onSubmit={handleEmailSubmit} className="flex flex-col gap-2">
                                <Input
                                    type="email"
                                    name="email"
                                    placeholder="Enter your email"
                                    autoFocus
                                    required
                                    className="bg-white/5 border-white/10 text-white placeholder:text-white/30 focus:border-violet-500/50 focus:ring-violet-500/20 rounded-xl"
                                />
                                <div className="flex gap-2">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setEmailFormOpen(false)}
                                        className="flex-1 text-white/50 hover:text-white/80"
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        type="submit"
                                        size="sm"
                                        disabled={pending}
                                        className="flex-1 bg-violet-600 hover:bg-violet-500 text-white"
                                    >
                                        {pending ? <Loader2 size={14} className="animate-spin" /> : 'Send Link'}
                                    </Button>
                                </div>
                            </form>
                        )}

                        {/* Error */}
                        {error && (
                            <p className="text-xs text-red-400/80 text-center mt-1">{error}</p>
                        )}
                    </div>
                )}

                {/* Footer */}
                <p className="text-center text-[10px] text-white/20 mt-6 leading-relaxed">
                    By continuing you agree to our Terms of Service and Privacy Policy
                </p>
            </div>
        </main>
    );
}
