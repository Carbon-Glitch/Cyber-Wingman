"use client";

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Image, Mic, Send, Sparkles, X, Zap, Rocket, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ChatMode = 'fast' | 'wingman' | 'crew';

interface ChatInputProps {
  onSend: (message: string) => void;
  onImageUpload?: (file: File) => void;
  characterColor: string;
  placeholder?: string;
  disabled?: boolean;
  mode?: ChatMode;
  onModeChange?: (mode: ChatMode) => void;
  media?: string[];
  onRemoveMedia?: (index: number) => void;
}

export function ChatInput({ 
  onSend, 
  onImageUpload, 
  characterColor, 
  placeholder = "Send message...",
  disabled = false,
  mode = 'wingman',
  onModeChange,
  media = [],
  onRemoveMedia
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getColorClass = () => {
    switch (characterColor) {
      case 'cyan': return 'border-cyber-cyan/30 focus:border-cyber-cyan/60';
      case 'amber': return 'border-cyber-amber/30 focus:border-cyber-amber/60';
      case 'purple': return 'border-cyber-purple/30 focus:border-cyber-purple/60';
      default: return 'border-cyber-pink/30 focus:border-cyber-pink/60';
    }
  };

  const getGlowClass = () => {
    switch (characterColor) {
      case 'cyan': return 'focus:shadow-[0_0_20px_rgba(0,240,255,0.15)]';
      case 'amber': return 'focus:shadow-[0_0_20px_rgba(255,170,0,0.15)]';
      case 'purple': return 'focus:shadow-[0_0_20px_rgba(184,41,221,0.15)]';
      default: return 'focus:shadow-[0_0_20px_rgba(255,0,122,0.15)]';
    }
  };

  const getButtonGradient = () => {
    switch (characterColor) {
      case 'cyan': return 'from-cyber-cyan to-[#00a0ff]';
      case 'amber': return 'from-cyber-amber to-[#ff7700]';
      case 'purple': return 'from-cyber-purple to-[#7729dd]';
      default: return 'from-cyber-pink to-[#ff00a0]';
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleImageClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onImageUpload) {
      onImageUpload(file);
    }
    e.target.value = '';
  };

  const cycleMode = () => {
    if (!onModeChange) return;
    const next = mode === 'fast' ? 'wingman' : mode === 'wingman' ? 'crew' : 'fast';
    onModeChange(next);
  };

  const getModeIcon = () => {
    switch (mode) {
      case 'fast': return <Zap className="w-3.5 h-3.5" />;
      case 'crew': return <Users className="w-3.5 h-3.5" />;
      default: return <Rocket className="w-3.5 h-3.5" />;
    }
  };

  const getModeLabel = () => {
    switch (mode) {
      case 'fast': return 'FAST';
      case 'crew': return 'CREW';
      default: return 'WINGMAN';
    }
  };

  const getModeStyle = () => {
    switch (mode) {
      case 'fast':
        return "bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 border-amber-500/20";
      case 'crew':
        return "bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 border-emerald-500/20";
      default:
        return "bg-cyber-pink/15 text-cyber-pink hover:bg-cyber-pink/25 border-cyber-pink/20";
    }
  };

  const quickActions = [
    { id: 'screenshot', label: 'Analyze Screenshot', icon: Image },
    { id: 'reply', label: 'Generate Reply', icon: Sparkles },
  ];

  return (
    <div className="relative">
      {/* Quick Actions Popup */}
      <AnimatePresence>
        {showQuickActions && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-full left-0 right-0 mb-2 px-4"
          >
            <div className="flex gap-2 justify-center">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <motion.button
                    key={action.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      setMessage(action.label + ': ');
                      setShowQuickActions(false);
                      textareaRef.current?.focus();
                    }}
                    className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.05] border border-white/10 text-sm text-neutral-02 hover:text-white hover:bg-white/[0.08] transition-colors"
                  >
                    <Icon className="w-4 h-4" />
                    {action.label}
                  </motion.button>
                );
              })}
              <button 
                onClick={() => setShowQuickActions(false)}
                className="p-2 rounded-full bg-white/[0.05] border border-white/10 text-neutral-03 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hidden file input */}
      <input 
        type="file" 
        accept="image/*" 
        className="hidden" 
        ref={fileInputRef}
        onChange={handleFileChange}
      />

      {/* Media Previews */}
      {media.length > 0 && (
        <div className="flex gap-3 px-4 pb-3 overflow-x-auto">
          {media.map((img, i) => (
            <div key={i} className="relative shrink-0 group">
              <img src={img} alt="preview" className="h-16 w-16 object-cover rounded-xl border border-white/10 shadow-sm" />
              {onRemoveMedia && (
                <button
                  onClick={() => onRemoveMedia(i)}
                  className="absolute -top-2 -right-2 bg-cyber-darker text-white border border-white/20 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-cyber-pink"
                >
                  <X size={12} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Input Container */}
      <div className={`
        mx-4 lg:mx-8 mb-6
        bg-[#121216]/90 backdrop-blur-xl
        border rounded-2xl
        transition-all duration-300
        ${getColorClass()} ${getGlowClass()}
        ${isFocused ? 'shadow-lg' : ''}
      `}>
        <div className="p-4">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="
              w-full bg-transparent border-none resize-none
              text-sm text-white placeholder-neutral-04
              focus:outline-none focus:ring-0
              min-h-[24px] max-h-[200px]
              disabled:opacity-50
            "
          />

          {/* Toolbar */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
            {/* Left Actions */}
            <div className="flex items-center gap-2">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleImageClick}
                disabled={disabled}
                className="p-2 rounded-lg text-neutral-04 hover:text-white hover:bg-white/[0.05] transition-colors disabled:opacity-50"
                title="Upload Image"
              >
                <Image className="w-5 h-5" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                disabled={disabled}
                className="p-2 rounded-lg text-neutral-04 hover:text-white hover:bg-white/[0.05] transition-colors disabled:opacity-50"
                title="Voice Input"
              >
                <Mic className="w-5 h-5" />
              </motion.button>

              <div className="w-px h-5 bg-white/10 mx-1" />

              {/* Mode Toggle */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={cycleMode}
                disabled={disabled}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border",
                  getModeStyle()
                )}
                title={`Mode: ${getModeLabel()}`}
              >
                {getModeIcon()}
                <span className="hidden sm:inline">{getModeLabel()}</span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowQuickActions(!showQuickActions)}
                disabled={disabled}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-neutral-04 hover:text-white hover:bg-white/[0.05] transition-colors disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Quick Actions
              </motion.button>
            </div>

            {/* Send Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSend}
              disabled={!message.trim() || disabled}
              className={`
                flex items-center gap-2 px-5 py-2 rounded-full
                bg-gradient-to-r ${getButtonGradient()}
                text-white text-xs font-bold uppercase tracking-widest
                transition-all duration-300
                disabled:opacity-50 disabled:cursor-not-allowed
                ${message.trim() ? 'shadow-lg' : ''}
              `}
            >
              Send
              <Send className="w-4 h-4" />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
}
