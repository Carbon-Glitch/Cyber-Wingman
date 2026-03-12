"use client";

import { motion } from 'framer-motion';
import { Bell, Crown, Shield } from 'lucide-react';

interface ChatHeaderProps {
  characterName: string;
  characterTitle: string;
  characterColor: string;
  protocolName: string;
  userName?: string;
}

export function ChatHeader({ 
  characterName, 
  characterTitle, 
  characterColor, 
  protocolName,
  userName = "Guest_77"
}: ChatHeaderProps) {
  const getColorClass = () => {
    switch (characterColor) {
      case 'cyan': return 'text-cyber-cyan';
      case 'amber': return 'text-cyber-amber';
      case 'purple': return 'text-cyber-purple';
      default: return 'text-cyber-pink';
    }
  };

  const getBgClass = () => {
    switch (characterColor) {
      case 'cyan': return 'bg-cyber-cyan';
      case 'amber': return 'bg-cyber-amber';
      case 'purple': return 'bg-cyber-purple';
      default: return 'bg-cyber-pink';
    }
  };

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/5 bg-cyber-black/50 backdrop-blur-xl sticky top-0 z-20">
      {/* Left: Protocol Info */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Shield className={`w-4 h-4 ${getColorClass()}`} />
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-[0.2em] ${getColorClass()}`}>
              Active Protocol
            </p>
            <p className="text-[9px] font-mono text-neutral-03">
              {protocolName}
            </p>
          </div>
        </div>
      </div>

      {/* Center: Character Badge */}
      <div className="hidden md:flex items-center gap-3">
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/[0.03] border border-white/10">
          <Crown className={`w-3.5 h-3.5 ${getColorClass()}`} />
          <span className="text-xs font-medium text-white">{characterName}</span>
          <span className="text-[10px] text-neutral-03">|</span>
          <span className="text-[10px] text-neutral-03">{characterTitle}</span>
        </div>
      </div>

      {/* Right: User Profile */}
      <div className="flex items-center gap-4">
        {/* Notification */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="relative p-2 rounded-lg hover:bg-white/[0.05] text-neutral-03 hover:text-white transition-colors"
        >
          <Bell className="w-5 h-5" />
          <span className={`absolute top-1.5 right-1.5 w-2 h-2 rounded-full ${getBgClass()}`} />
        </motion.button>

        {/* User Info */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-white">{userName}</p>
            <p className={`text-[9px] uppercase tracking-widest font-bold ${getColorClass()}`}>
              Pro Account
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl overflow-hidden border border-white/10 bg-gradient-to-br from-white/10 to-transparent">
            <div className="w-full h-full flex items-center justify-center text-lg font-bold text-neutral-03">
              {userName.charAt(0).toUpperCase()}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
