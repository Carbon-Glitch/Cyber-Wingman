"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';
import { Loader2, X, UserCircle, Settings2, ShieldAlert } from 'lucide-react';

interface ProfileModalProps {
    isOpen: boolean;
    onClose?: () => void;
    sessionToken: string;
    userId: string;
    onProfileUpdated: () => void;
    forceMandatory?: boolean; // If true, user cannot close without filling mandatory fields
}

export function ProfileModal({ isOpen, onClose, sessionToken, userId, onProfileUpdated, forceMandatory }: ProfileModalProps) {
    const supabase = createSupabaseBrowserClient();
    
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Form State
    const [formData, setFormData] = useState({
        username: '',
        gender: '',
        relationship_status: '',
        age: '',
        occupation: '',
        religion: '',
        social_media: '',
        financial_status: '',
        mbti: '',
        core_personality: '',
        ideal_type: '',
        current_challenge: '',
        wingman_goal: '',
        deal_breakers: ''
    });

    useEffect(() => {
        if (!isOpen || !userId) return;

        async function fetchProfile() {
            try {
                const { data, error } = await supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', userId)
                    .single();

                if (data) {
                    setFormData({
                        username: data.username || '',
                        gender: data.gender || '',
                        relationship_status: data.relationship_status || '',
                        age: data.age || '',
                        occupation: data.occupation || '',
                        religion: data.religion || '',
                        social_media: data.social_media || '',
                        financial_status: data.financial_status || '',
                        mbti: data.mbti || '',
                        core_personality: data.core_personality || '',
                        ideal_type: data.ideal_type || '',
                        current_challenge: data.current_challenge || '',
                        wingman_goal: data.wingman_goal || '',
                        deal_breakers: data.deal_breakers || ''
                    });
                }
            } catch (err) {
                console.error("Failed to load profile", err);
            } finally {
                setIsLoading(false);
            }
        }
        fetchProfile();
    }, [isOpen, userId, supabase]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setIsSaving(true);

        // Basic Validation for mandatory fields
        if (!formData.username.trim() || !formData.gender || !formData.relationship_status) {
            setError("ID, Gender, and Relationship Status are mandatory.");
            setIsSaving(false);
            return;
        }

        try {
            const { error: upsertError } = await supabase
                .from('profiles')
                .upsert({
                    id: userId,
                    ...formData,
                    updated_at: new Date().toISOString(),
                });

            if (upsertError) throw upsertError;

            setSuccess("Profile synchronized successfully.");
            onProfileUpdated();
            
            if (onClose && !forceMandatory) {
                setTimeout(onClose, 1500);
            }
        } catch (err: any) {
            setError(err.message || 'Failed to save profile.');
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 overflow-hidden">
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/80 backdrop-blur-md"
                onClick={() => {
                    if (!forceMandatory && onClose) onClose();
                }}
            />

            {/* Modal Card */}
            <motion.div 
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative z-10 w-full max-w-4xl max-h-[90vh] flex flex-col bg-gray-950 border border-cyber-pink/30 rounded-2xl shadow-[0_0_50px_rgba(255,42,133,0.1)] overflow-hidden"
            >
                {/* Header */}
                <div className="flex-shrink-0 flex items-center justify-between p-6 border-b border-white/10 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyber-cyan via-cyber-pink to-cyber-purple" />
                    
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-cyber-pink/10 border border-cyber-pink/40 flex items-center justify-center text-cyber-pink">
                            <Settings2 size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-black italic tracking-widest uppercase text-white">Subject Profile</h2>
                            <p className="text-xs font-mono text-neutral-04 tracking-widest mt-1">Calibrating AI Context Parameters</p>
                        </div>
                    </div>

                    {!forceMandatory && onClose && (
                        <button 
                            onClick={onClose}
                            className="p-2 text-neutral-04 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                        >
                            <X size={20} />
                        </button>
                    )}
                </div>

                {isLoading ? (
                    <div className="flex-1 flex flex-col items-center justify-center py-32 space-y-4">
                        <Loader2 className="w-8 h-8 text-cyber-pink animate-spin" />
                        <p className="text-xs font-mono tracking-widest text-neutral-04 uppercase">Extracting Profile Data...</p>
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
                        <form id="profile-form" onSubmit={handleSave} className="p-6 sm:p-8 space-y-10">
                            
                            {forceMandatory && (
                                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-4">
                                    <ShieldAlert className="w-5 h-5 text-amber-400 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-bold text-amber-400">INITIALIZATION REQUIRED</p>
                                        <p className="text-xs text-amber-400/80 mt-1">Provide mandatory identity parameters to unlock the chat interface.</p>
                                    </div>
                                </div>
                            )}

                            {/* Section: Core Identity (MANDATORY) */}
                            <div className="space-y-6">
                                <div className="flex items-center gap-3 border-b border-white/10 pb-2">
                                    <UserCircle className="w-5 h-5 text-cyber-cyan" />
                                    <h3 className="text-sm font-black italic tracking-[0.2em] text-cyber-cyan uppercase">Core Identity (Required)</h3>
                                </div>
                                
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">ID / Handle *</label>
                                        <input 
                                            type="text" name="username" value={formData.username} onChange={handleChange} required
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-cyan outline-none transition-colors"
                                            placeholder="e.g. Neo"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Gender *</label>
                                        <select 
                                            name="gender" value={formData.gender} onChange={handleChange} required
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-cyan outline-none transition-colors appearance-none"
                                        >
                                            <option value="" disabled>Select...</option>
                                            <option value="Male">Male</option>
                                            <option value="Female">Female</option>
                                            <option value="Other">Other</option>
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Status *</label>
                                        <select 
                                            name="relationship_status" value={formData.relationship_status} onChange={handleChange} required
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-cyan outline-none transition-colors appearance-none"
                                        >
                                            <option value="" disabled>Select...</option>
                                            <option value="Single">Single</option>
                                            <option value="Situationship">Situationship</option>
                                            <option value="In a relationship">In a relationship</option>
                                            <option value="Married">Married</option>
                                            <option value="Divorced">Divorced</option>
                                            <option value="Complicated">It's Complicated</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Section: Demographics & Lifestyle */}
                            <div className="space-y-6">
                                <div className="border-b border-white/10 pb-2">
                                    <h3 className="text-sm font-black italic tracking-[0.2em] text-white/60 uppercase">Demographics & Lifestyle</h3>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Age</label>
                                        <input 
                                            type="text" name="age" value={formData.age} onChange={handleChange}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-pink outline-none transition-colors"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Occupation</label>
                                        <input 
                                            type="text" name="occupation" value={formData.occupation} onChange={handleChange}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-pink outline-none transition-colors"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Religion/Values</label>
                                        <input 
                                            type="text" name="religion" value={formData.religion} onChange={handleChange}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-pink outline-none transition-colors"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Social Media Vibes</label>
                                        <input 
                                            type="text" name="social_media" value={formData.social_media} onChange={handleChange}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-pink outline-none transition-colors"
                                            placeholder="e.g. Active IG, Lowkey"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Financial Status</label>
                                        <input 
                                            type="text" name="financial_status" value={formData.financial_status} onChange={handleChange}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-pink outline-none transition-colors"
                                            placeholder="e.g. Stable, Hustling"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">MBTI</label>
                                        <input 
                                            type="text" name="mbti" value={formData.mbti} onChange={handleChange}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-pink outline-none transition-colors"
                                            placeholder="e.g. INTJ"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Section: Psychological Profiling */}
                            <div className="space-y-6">
                                <div className="border-b border-white/10 pb-2">
                                    <h3 className="text-sm font-black italic tracking-[0.2em] text-white/60 uppercase">Psychological Profiling</h3>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Core Personality Traits</label>
                                        <textarea 
                                            name="core_personality" value={formData.core_personality} onChange={handleChange}
                                            rows={2}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-purple outline-none transition-colors resize-none custom-scrollbar"
                                            placeholder="How would your friends describe you?"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Ideal Type (Physical & Mental)</label>
                                        <textarea 
                                            name="ideal_type" value={formData.ideal_type} onChange={handleChange}
                                            rows={2}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-purple outline-none transition-colors resize-none custom-scrollbar"
                                            placeholder="What exactly are you looking for?"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Current Top Relationship Challenge</label>
                                        <textarea 
                                            name="current_challenge" value={formData.current_challenge} onChange={handleChange}
                                            rows={2}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-purple outline-none transition-colors resize-none custom-scrollbar"
                                            placeholder="e.g. Always getting ghosted, Marriage lacks spark"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">Deal Breakers (The "Red Flags")</label>
                                        <textarea 
                                            name="deal_breakers" value={formData.deal_breakers} onChange={handleChange}
                                            rows={2}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-purple outline-none transition-colors resize-none custom-scrollbar"
                                            placeholder="What can you absolutely not tolerate?"
                                        />
                                    </div>
                                </div>
                                
                                <div className="space-y-2">
                                    <label className="text-[10px] font-mono tracking-widest text-neutral-03 uppercase">What goal do you want the AI Wingman to help you achieve?</label>
                                    <textarea 
                                        name="wingman_goal" value={formData.wingman_goal} onChange={handleChange}
                                        rows={3}
                                        className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-cyber-purple outline-none transition-colors resize-none custom-scrollbar"
                                        placeholder="e.g. Find a long-term partner, get my ex back, learn how to flirt..."
                                    />
                                </div>
                            </div>

                        </form>
                    </div>
                )}

                {/* Footer Actions */}
                <div className="flex-shrink-0 p-6 border-t border-white/10 bg-gray-950/80 backdrop-blur-md">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="text-[10px] font-mono tracking-widest uppercase">
                            {error && <span className="text-red-400">{error}</span>}
                            {success && <span className="text-cyber-cyan">{success}</span>}
                            {!error && !success && <span className="text-neutral-04">Data securely stored in neural net.</span>}
                        </div>
                        <button
                            form="profile-form"
                            type="submit"
                            disabled={isLoading || isSaving}
                            className="w-full sm:w-auto px-8 py-3 rounded-xl bg-cyber-pink text-black font-black italic tracking-widest uppercase text-sm hover:brightness-110 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {isSaving && <Loader2 size={16} className="animate-spin" />}
                            {isSaving ? 'SYNCING...' : 'SYNC NEURAL PROFILE'}
                        </button>
                    </div>
                </div>

            </motion.div>
        </div>
    );
}
