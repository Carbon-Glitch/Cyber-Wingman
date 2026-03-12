"use client";

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Settings, 
  BarChart3, 
  Zap, 
  MessageSquare, 
  ChevronRight,
  Trash2,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  unread?: boolean;
}

interface ChatSidebarProps {
  characterName: string;
  characterColor: string;
  characterTitle: string;
  onNewSession: () => void;
  sessions: ChatSession[];
  activeSessionId: string;
  onSwitchSession: (id: string) => void;
  onDeleteSession?: (id: string, e: React.MouseEvent) => void;
  onOpenSettings?: () => void;
}

const tools = [
  { id: 'screenshot', name: 'Screenshot Analysis', icon: MessageSquare, description: 'Analyze chat screenshots' },
  { id: 'reply', name: 'Reply Generator', icon: Zap, description: 'Get perfect responses' },
  { id: 'insights', name: 'Insights', icon: BarChart3, description: 'View your patterns' },
];

export function ChatSidebar({ 
  characterName, 
  characterColor, 
  characterTitle,
  onNewSession,
  sessions,
  activeSessionId,
  onSwitchSession,
  onDeleteSession,
  onOpenSettings
}: ChatSidebarProps) {
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState(true);

  const getColorClass = () => {
    switch (characterColor) {
      case 'cyan': return 'text-cyber-cyan border-cyber-cyan/50';
      case 'amber': return 'text-cyber-amber border-cyber-amber/50';
      case 'purple': return 'text-cyber-purple border-cyber-purple/50';
      default: return 'text-cyber-pink border-cyber-pink/50';
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

  const getGlowClass = () => {
    switch (characterColor) {
      case 'cyan': return 'shadow-[0_0_20px_rgba(0,240,255,0.3)]';
      case 'amber': return 'shadow-[0_0_20px_rgba(255,170,0,0.3)]';
      case 'purple': return 'shadow-[0_0_20px_rgba(184,41,221,0.3)]';
      default: return 'shadow-[0_0_20px_rgba(255,0,122,0.3)]';
    }
  };

  // Group sessions by date
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;
  
  const todaySessions = sessions.filter(s => now - s.createdAt < oneDay);
  const yesterdaySessions = sessions.filter(s => {
    const diff = now - s.createdAt;
    return diff >= oneDay && diff < 2 * oneDay;
  });
  const olderSessions = sessions.filter(s => now - s.createdAt >= 2 * oneDay);

  return (
    <aside className="w-72 flex-shrink-0 bg-cyber-darker border-r border-white/5 flex flex-col h-full">
      {/* Logo Section */}
      <div className="p-5 border-b border-white/5">
        <a href="/" className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg ${getBgClass()} flex items-center justify-center font-bold text-cyber-black italic ${getGlowClass()}`}>
            {characterName.charAt(0)}
          </div>
          <div>
            <h1 className={`text-lg font-black tracking-tighter italic ${getColorClass().split(' ')[0]}`}>
              {characterName.toUpperCase()}
            </h1>
            <p className="text-[9px] text-neutral-03 uppercase tracking-widest">{characterTitle}</p>
          </div>
        </a>
      </div>

      {/* New Session Button */}
      <div className="p-4">
        <motion.button
          onClick={onNewSession}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            w-full py-3 px-4 rounded-xl border flex items-center justify-center gap-2
            transition-all duration-300 group
            ${getColorClass()} bg-white/[0.02] hover:bg-white/[0.05]
          `}
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm font-medium">New Session</span>
        </motion.button>
      </div>

      {/* Tools Section */}
      <div className="px-4 pb-4">
        <button
          onClick={() => setExpandedTools(!expandedTools)}
          className="flex items-center justify-between w-full text-[10px] uppercase tracking-widest text-neutral-03 font-bold mb-3 hover:text-white transition-colors"
        >
          <span>Quick Tools</span>
          <ChevronRight className={`w-3 h-3 transition-transform ${expandedTools ? 'rotate-90' : ''}`} />
        </button>
        
        <AnimatePresence>
          {expandedTools && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="space-y-2"
            >
              {tools.map((tool) => {
                const Icon = tool.icon;
                return (
                  <motion.button
                    key={tool.id}
                    onClick={() => setActiveTool(activeTool === tool.id ? null : tool.id)}
                    whileHover={{ x: 4 }}
                    className={`
                      w-full flex items-center gap-3 p-3 rounded-lg text-left
                      transition-all duration-200 group
                      ${activeTool === tool.id 
                        ? `bg-white/10 ${getColorClass().split(' ')[0]}` 
                        : 'text-neutral-03 hover:text-white hover:bg-white/[0.03]'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{tool.name}</p>
                      <p className="text-[10px] opacity-60 truncate">{tool.description}</p>
                    </div>
                  </motion.button>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Session History */}
      <div className="flex-1 overflow-y-auto px-4">
        {/* Today */}
        {todaySessions.length > 0 && (
          <div className="mb-6">
            <p className="text-[10px] uppercase tracking-widest text-neutral-03 font-bold mb-3">Today</p>
            <ul className="space-y-1">
              {todaySessions.map((session) => (
                <li key={session.id}>
                  <button 
                    onClick={() => onSwitchSession(session.id)}
                    className={cn(
                      "w-full flex items-center gap-2 p-2 rounded-lg text-left group transition-colors",
                      session.id === activeSessionId 
                        ? "bg-white/10 text-white" 
                        : "hover:bg-white/[0.03] text-neutral-02"
                    )}
                  >
                    <MessageSquare className={cn(
                      "w-3.5 h-3.5 transition-colors",
                      session.id === activeSessionId ? "text-white" : "text-neutral-04 group-hover:text-white"
                    )} />
                    <span className="text-sm truncate flex-1">{session.title}</span>
                    {session.unread && (
                      <span className={`w-1.5 h-1.5 rounded-full ${getBgClass()}`} />
                    )}
                    {onDeleteSession && session.id !== activeSessionId && (
                      <span
                        onClick={(e) => onDeleteSession(session.id, e)}
                        className="hidden group-hover:flex items-center justify-center text-neutral-04 hover:text-red-400 transition-colors shrink-0"
                      >
                        <Trash2 className="w-3 h-3" />
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Yesterday */}
        {yesterdaySessions.length > 0 && (
          <div className="mb-6">
            <p className="text-[10px] uppercase tracking-widest text-neutral-03 font-bold mb-3">Yesterday</p>
            <ul className="space-y-1">
              {yesterdaySessions.map((session) => (
                <li key={session.id}>
                  <button 
                    onClick={() => onSwitchSession(session.id)}
                    className={cn(
                      "w-full flex items-center gap-2 p-2 rounded-lg text-left group transition-colors",
                      session.id === activeSessionId 
                        ? "bg-white/10 text-white" 
                        : "hover:bg-white/[0.03] text-neutral-02"
                    )}
                  >
                    <MessageSquare className={cn(
                      "w-3.5 h-3.5 transition-colors",
                      session.id === activeSessionId ? "text-white" : "text-neutral-04 group-hover:text-white"
                    )} />
                    <span className="text-sm truncate flex-1">{session.title}</span>
                    {session.unread && (
                      <span className={`w-1.5 h-1.5 rounded-full ${getBgClass()}`} />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Older */}
        {olderSessions.length > 0 && (
          <div className="mb-6">
            <p className="text-[10px] uppercase tracking-widest text-neutral-03 font-bold mb-3">Older</p>
            <ul className="space-y-1">
              {olderSessions.map((session) => (
                <li key={session.id}>
                  <button 
                    onClick={() => onSwitchSession(session.id)}
                    className={cn(
                      "w-full flex items-center gap-2 p-2 rounded-lg text-left group transition-colors",
                      session.id === activeSessionId 
                        ? "bg-white/10 text-white" 
                        : "hover:bg-white/[0.03] text-neutral-02"
                    )}
                  >
                    <MessageSquare className={cn(
                      "w-3.5 h-3.5 transition-colors",
                      session.id === activeSessionId ? "text-white" : "text-neutral-04 group-hover:text-white"
                    )} />
                    <span className="text-sm truncate flex-1">{session.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Bottom Status */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${getBgClass()} animate-pulse`} />
            <span className="text-[10px] tracking-widest text-neutral-03 uppercase">System Online</span>
          </div>
          <button 
            onClick={onOpenSettings}
            className="p-2 rounded-lg hover:bg-white/[0.05] text-neutral-03 hover:text-white transition-colors"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
