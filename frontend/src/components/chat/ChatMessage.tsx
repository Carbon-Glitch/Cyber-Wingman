"use client";

import { motion } from 'framer-motion';
import { Copy, RefreshCw, Check, Bot, Sparkles, Zap, Users, Cpu, Wrench, Brain } from 'lucide-react';
import { useState } from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  media?: string[];
  timestamp?: Date;
  isThinking?: boolean;
  thinking?: string;
  toolSteps?: ToolStep[];
  activatedSkills?: string[];
  subagentSpawned?: { id: string; task: string }[];
  thoughts?: ThoughtStep[];
  currentStep?: string;
  isDone?: boolean;
  replyOptions?: string[];
  replyAnalysis?: string;
  // Crew mode
  crewTasks?: CrewTask[];
  crewPhase?: 'plan' | 'dispatch' | 'synthesize' | 'done';
  crewPlanSummary?: string;
}

export interface ToolStep {
  id: string;
  toolName: string;
  status: 'running' | 'success' | 'error';
  args?: Record<string, unknown>;
}

export interface ThoughtStep {
  step: string;
  content: string;
  timestamp?: string;
}

export interface CrewTask {
  id: number;
  subject: string;
  status: 'pending' | 'running' | 'done';
}

interface ChatMessageProps {
  message: Message;
  characterImage: string;
  characterColor: string;
  characterName: string;
  mode?: 'fast' | 'wingman' | 'crew';
}

export function ChatMessage({ 
  message, 
  characterImage, 
  characterColor, 
  characterName,
  mode = 'wingman'
}: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const isUser = message.role === 'user';

  const getColorClass = () => {
    switch (characterColor) {
      case 'cyan': return 'border-cyber-cyan/30 bg-cyber-cyan/5';
      case 'amber': return 'border-cyber-amber/30 bg-cyber-amber/5';
      case 'purple': return 'border-cyber-purple/30 bg-cyber-purple/5';
      default: return 'border-cyber-pink/30 bg-cyber-pink/5';
    }
  };

  const getAccentColor = () => {
    switch (characterColor) {
      case 'cyan': return 'text-cyber-cyan';
      case 'amber': return 'text-cyber-amber';
      case 'purple': return 'text-cyber-purple';
      default: return 'text-cyber-pink';
    }
  };

  const getBorderColor = () => {
    switch (characterColor) {
      case 'cyan': return 'border-cyber-cyan';
      case 'amber': return 'border-cyber-amber';
      case 'purple': return 'border-cyber-purple';
      default: return 'border-cyber-pink';
    }
  };

  const getGlowColor = () => {
    switch (characterColor) {
      case 'cyan': return 'shadow-[0_0_20px_rgba(0,240,255,0.2)]';
      case 'amber': return 'shadow-[0_0_20px_rgba(255,170,0,0.2)]';
      case 'purple': return 'shadow-[0_0_20px_rgba(184,41,221,0.2)]';
      default: return 'shadow-[0_0_20px_rgba(255,0,122,0.2)]';
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // User Message
  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20, x: 20 }}
        animate={{ opacity: 1, y: 0, x: 0 }}
        transition={{ duration: 0.4, ease: [0.19, 1, 0.22, 1] }}
        className="flex justify-end"
      >
        <div className="max-w-[80%] lg:max-w-[70%]">
          {/* Media attachments */}
          {message.media && message.media.length > 0 && (
            <div className="flex gap-2 mb-3 flex-wrap justify-end">
              {message.media.map((img, i) => (
                <img 
                  key={i} 
                  src={img} 
                  alt="attachment" 
                  className="h-24 w-auto rounded-xl border border-white/10 object-cover shadow-sm" 
                />
              ))}
            </div>
          )}
          <div className="bg-white/[0.05] border border-white/10 rounded-2xl rounded-tr-sm px-5 py-4">
            <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
          <p className="text-[10px] text-neutral-04 mt-2 text-right">
            {message.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) || 
             new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </motion.div>
    );
  }

  // AI Message
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, x: -20 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      transition={{ duration: 0.4, ease: [0.19, 1, 0.22, 1] }}
      className="flex items-start gap-4"
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-10 h-10 rounded-xl border overflow-hidden ${getBorderColor()}/50 ${getGlowColor()}`}>
        <img 
          src={characterImage} 
          alt={characterName}
          className="w-full h-full object-cover object-top"
        />
      </div>

      {/* Message Content */}
      <div className="flex-1 max-w-[85%] lg:max-w-[75%] group">
        {/* Mode Badge */}
        {mode === 'fast' && message.isDone && (
          <div className="inline-flex items-center gap-1 text-[10px] text-amber-400/70 mb-2">
            <Zap size={10} /><span className="uppercase tracking-wider">Fast Mode</span>
          </div>
        )}
        {mode === 'crew' && (
          <div className="inline-flex items-center gap-1 text-[10px] text-emerald-400/70 mb-2">
            <Users size={10} /><span className="uppercase tracking-wider">Crew Mode</span>
          </div>
        )}

        <div className={`
          relative p-5 rounded-2xl rounded-tl-sm
          border backdrop-blur-sm
          ${getColorClass()}
        `}>
          {/* Accent Line */}
          <div className={`absolute top-0 left-0 w-1 h-full ${getBorderColor()} rounded-l-2xl`} />
          
          {/* Crew Plan Card */}
          {message.crewTasks && message.crewTasks.length > 0 && (
            <div className="mb-4 p-3 rounded-lg bg-black/20 border border-white/5">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-bold">
                  Execution Plan
                </span>
              </div>
              {message.crewPlanSummary && (
                <p className="text-xs text-neutral-03 mb-2">{message.crewPlanSummary}</p>
              )}
              <div className="space-y-1">
                {message.crewTasks.map((task) => (
                  <div key={task.id} className="flex items-center gap-2 text-xs">
                    <div className={cn(
                      "w-1.5 h-1.5 rounded-full",
                      task.status === 'done' ? "bg-emerald-400" :
                      task.status === 'running' ? "bg-amber-400 animate-pulse" :
                      "bg-neutral-04"
                    )} />
                    <span className={cn(
                      "flex-1",
                      task.status === 'done' ? "text-neutral-02 line-through" :
                      task.status === 'running' ? "text-white" :
                      "text-neutral-04"
                    )}>
                      {task.subject}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills Activated */}
          {mode !== 'fast' && message.activatedSkills && message.activatedSkills.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-1.5">
              {message.activatedSkills.map((skill, i) => (
                <span 
                  key={i}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-white/5 text-neutral-02 border border-white/10"
                >
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  {skill}
                </span>
              ))}
            </div>
          )}

          {/* Subagents */}
          {mode === 'wingman' && message.subagentSpawned && message.subagentSpawned.length > 0 && (
            <div className="mb-3 space-y-1">
              {message.subagentSpawned.map((sub, i) => (
                <div key={i} className="flex items-center gap-2 text-[10px] text-neutral-03">
                  <Bot className="w-3 h-3 text-cyber-cyan" />
                  <span className="uppercase tracking-wider">Subagent:</span>
                  <span className="text-neutral-02 truncate">{sub.task}</span>
                </div>
              ))}
            </div>
          )}

          {/* Thinking Indicator */}
          {message.isThinking && message.thinking && (
            <div className="mb-3 flex items-center gap-2 text-[10px] text-neutral-03 italic">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              >
                <Brain className="w-3.5 h-3.5" />
              </motion.div>
              <span className="animate-pulse">{message.thinking}</span>
            </div>
          )}

          {/* Tool Steps */}
          {mode !== 'fast' && message.toolSteps && message.toolSteps.length > 0 && (
            <div className="mb-3 space-y-1">
              {message.toolSteps.map((step) => (
                <div 
                  key={step.id}
                  className="flex items-center gap-2 text-[10px]"
                >
                  <Wrench className={cn(
                    "w-3 h-3",
                    step.status === 'running' ? "text-amber-400 animate-pulse" :
                    step.status === 'success' ? "text-emerald-400" :
                    "text-red-400"
                  )} />
                  <span className="text-neutral-03 uppercase tracking-wider">{step.toolName}</span>
                  <span className={cn(
                    "ml-auto",
                    step.status === 'running' ? "text-amber-400" :
                    step.status === 'success' ? "text-emerald-400" :
                    "text-red-400"
                  )}>
                    {step.status === 'running' ? 'Running...' :
                     step.status === 'success' ? 'Done' :
                     'Error'}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Thoughts Panel (Collapsible) */}
          {mode !== 'fast' && (message.thoughts || message.currentStep) && (
            <div className="mb-3">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center gap-2 text-[10px] text-neutral-04 hover:text-neutral-02 transition-colors mb-2"
              >
                <Brain className="w-3 h-3" />
                <span className="uppercase tracking-wider">Thinking Process</span>
                <span className="text-[8px]">{showDetails ? '▼' : '▶'}</span>
              </button>
              
              {showDetails && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="pl-3 border-l border-white/10 space-y-2"
                >
                  {message.currentStep && (
                    <div className="text-[10px] text-neutral-03">
                      <span className="text-amber-400">→</span> {message.currentStep}
                    </div>
                  )}
                  {message.thoughts?.map((thought, i) => (
                    <div key={i} className="text-[10px] text-neutral-03">
                      <span className={getAccentColor()}>{thought.step}:</span> {thought.content}
                    </div>
                  ))}
                </motion.div>
              )}
            </div>
          )}

          {/* Main Content */}
          {message.content && (
            <div 
              className="text-sm text-gray-200 leading-relaxed prose prose-invert prose-sm max-w-none"
              dangerouslySetInnerHTML={{ 
                __html: message.content
                  .replace(/<highlight>(.*?)<\/highlight>/g, `<span class="${getAccentClass(characterColor)} font-bold underline decoration-wavy underline-offset-4">$1</span>`)
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\*(.*?)\*/g, '<em>$1</em>')
                  .replace(/```([\s\S]*?)```/g, '<pre class="bg-black/30 p-2 rounded text-xs overflow-x-auto my-2"><code>$1</code></pre>')
                  .replace(/`([^`]+)`/g, '<code class="bg-black/30 px-1 rounded text-xs">$1</code>')
              }}
            />
          )}
        </div>

        {/* Action Buttons */}
        {message.isDone && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex items-center gap-4 mt-2 ml-1"
          >
            <button 
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase text-neutral-04 hover:text-white transition-colors"
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button className="flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase text-neutral-04 hover:text-white transition-colors">
              <RefreshCw className="w-3 h-3" />
              Regenerate
            </button>
          </motion.div>
        )}

        {/* Reply Suggestions */}
        {message.replyOptions && message.replyOptions.length > 0 && (
          <div className="mt-4 space-y-2">
            {message.replyAnalysis && (
              <p className="text-[10px] text-neutral-04 mb-2 italic">{message.replyAnalysis}</p>
            )}
            <p className="text-[10px] uppercase tracking-widest text-neutral-04 mb-2">
              Suggested Responses
            </p>
            {message.replyOptions.map((option, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                whileHover={{ x: 4 }}
                className={`
                  w-full text-left p-3 rounded-lg text-sm
                  border transition-all duration-200
                  ${getColorClass()} hover:bg-white/[0.05]
                `}
              >
                <span className={`text-xs font-bold ${getAccentColor()} mr-2`}>{String.fromCharCode(65 + index)}.</span>
                {option}
              </motion.button>
            ))}
          </div>
        )}

        <p className="text-[10px] text-neutral-04 mt-2">
          {message.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) || 
           new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </motion.div>
  );
}

function getAccentClass(color: string) {
  switch (color) {
    case 'cyan': return 'text-cyber-cyan';
    case 'amber': return 'text-cyber-amber';
    case 'purple': return 'text-cyber-purple';
    default: return 'text-cyber-pink';
  }
}
