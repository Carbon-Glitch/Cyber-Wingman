"use client";

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';
import { ProfileModal } from '@/components/ProfileModal';
import { 
  ChatHeader, 
  ChatMessage, 
  ChatInput, 
  ChatSidebar, 
  TypingIndicator,
  type Message,
  type ChatMode,
  type ChatSession
} from '@/components/chat';

// ── Types ────────────────────────────────────────────────────

type ToolStepStatus = 'running' | 'success' | 'error';

type ToolStep = {
  id: string;
  toolName: string;
  status: ToolStepStatus;
  args?: Record<string, unknown>;
};

type ThoughtStep = {
  step: string;
  content: string;
  timestamp?: string;
};

type CrewTask = {
  id: number;
  subject: string;
  status: 'pending' | 'running' | 'done';
};

// ── Character Configurations ─────────────────────────────────

const CHARACTERS = {
  aphrodite: {
    id: 'aphrodite',
    name: 'Aphrodite',
    title: 'The Savage Bestie',
    color: 'pink' as const,
    image: '/images/Cyber Aphrodite.png',
    protocol: 'SECURE_CHANNEL : //APHRODITE_ALPHA_7',
    welcomeMessage: "Hey girl! I'm Aphrodite, your no-BS bestie. Paste a screenshot of that confusing text, tell me about your situation, or just vent. I'll give you the real tea and help you make power moves. What's going on?",
    traits: ['Hyper-Analytical', 'Zero BS'],
  },
  chiron: {
    id: 'chiron',
    name: 'Chiron',
    title: 'The Strategic Mentor',
    color: 'cyan' as const,
    image: '/images/Cyber Chiron.png',
    protocol: 'SECURE_CHANNEL : //CHIRON_BETA_3',
    welcomeMessage: "Welcome. I'm Chiron. I don't do fluff—I give you field-tested strategies that work. Share your situation, show me a conversation, and I'll break down exactly what you need to do next.",
    traits: ['Field-Tested', 'No Fluff'],
  },
  odysseus: {
    id: 'odysseus',
    name: 'Odysseus',
    title: 'The Marriage Architect',
    color: 'amber' as const,
    image: '/images/Cyber Odysseus.png',
    protocol: 'SECURE_CHANNEL : //ODYSSEUS_GAMMA_9',
    welcomeMessage: "I'm Odysseus. Marriage is a complex system, and I'm here to help you navigate it with strategic precision. Whether it's conflict resolution, long-term planning, or understanding dynamics—let's talk.",
    traits: ['Rational', 'Long-term'],
  },
  persephone: {
    id: 'persephone',
    name: 'Persephone',
    title: 'The Power Queen',
    color: 'purple' as const,
    image: '/images/Cyber Persephone.png',
    protocol: 'SECURE_CHANNEL : //PERSEPHONE_DELTA_5',
    welcomeMessage: "Hello. I'm Persephone. I understand power, control, and the games people play. If you want to maintain dominance in your relationship, I'll show you exactly how it's done. What's your situation?",
    traits: ['Calculated', 'Dominant'],
  },
};

type CharacterId = keyof typeof CHARACTERS;

// ── Session Types ───────────────────────────────────────────

type SessionItem = {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
  mode: ChatMode;
  characterId: CharacterId;
  isLoaded?: boolean;
};

// ── Helper Functions ────────────────────────────────────────

function makeSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function getDefaultCharacter(): CharacterId {
  // MOCK USER PROFILE for Auto-Routing (Local Dev specific: Default to Single Male)
  const mockUser = { gender: 'male', status: 'single' };
  if (mockUser.gender === 'male' && mockUser.status === 'single') return 'chiron';
  if (mockUser.gender === 'male' && mockUser.status === 'married') return 'odysseus';
  if (mockUser.gender === 'female' && mockUser.status === 'single') return 'aphrodite';
  return 'persephone';
}

function makeSession(overrides?: Partial<SessionItem>): SessionItem {
  const characterId = overrides?.characterId || getDefaultCharacter();
  
  return {
    id: makeSessionId(),
    title: 'New Session',
    createdAt: Date.now(),
    messages: [],
    mode: 'wingman',
    characterId,
    isLoaded: true,
    ...overrides,
  };
}

// ── Main Component ──────────────────────────────────────────

export default function ChatPage() {
  // Auth & Session State
  const [sessions, setSessions] = useState<SessionItem[]>(() => [makeSession()]);
  const [activeId, setActiveId] = useState<string>(() => sessions[0].id);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [isGuest, setIsGuest] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // UI State
  const [media, setMedia] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // New states for Profile and Setup
  const [userId, setUserId] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [forceSetup, setForceSetup] = useState(false);

  // Initialize Auth, Load Historical Sessions, and Profile
  const fetchProfile = async (supabaseApp: any, uid: string) => {
    try {
      const { data } = await supabaseApp.from('profiles').select('*').eq('id', uid).single();
      setUserProfile(data || null);
      if (!data || !data.username || !data.gender || !data.relationship_status) {
        setForceSetup(true);
        setShowProfileModal(true);
      } else {
        setForceSetup(false);
        // Optionally auto-close if it was forced
      }
    } catch (e) {
      console.error("Profile check error:", e);
      setForceSetup(true);
      setShowProfileModal(true);
    }
  };

  useEffect(() => {
    async function init() {
      const supabase = createSupabaseBrowserClient();
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      const uid = data.session?.user?.id;

      if (token && uid) {
        setSessionToken(token);
        setUserId(uid);
        setIsGuest(false);
        
        await fetchProfile(supabase, uid);

        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/chat/sessions`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const json = await res.json();
          if (json.sessions && json.sessions.length > 0) {
            const loaded: SessionItem[] = json.sessions.map((s: any) => ({
              id: s.key.split(':')[1],
              title: s.title,
              createdAt: new Date(s.created_at).getTime(),
              messages: [],
              mode: 'wingman',
              characterId: 'chiron',
              isLoaded: false
            }));
            setSessions(loaded);
            setActiveId(loaded[0].id);
          }
        } catch (e) {
          console.error('Failed to load sessions', e);
        }
      } else {
        // Since we redesigned auth, force them to login if guest
        // If guest clicks start in home, they go to /login. If they go straight to /chat,
        // we could let them read demo chats or redirect. Let's redirect if no session.
        window.location.href = '/login';
      }
    }
    init();
  }, []);

  // ... (keep auto-scroll and helpers)
  const activeSession = sessions.find(s => s.id === activeId) ?? sessions[0];
  const messages = activeSession?.messages ?? [];
  const mode = activeSession?.mode ?? 'wingman';
  const characterId = activeSession?.characterId ?? 'chiron';
  const character = CHARACTERS[characterId];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const updateSession = useCallback((id: string, updater: (s: SessionItem) => SessionItem) => {
    setSessions(prev => prev.map(s => s.id === id ? updater(s) : s));
  }, []);

  const updateAssistant = useCallback((sessionId: string, msgId: string, updater: (msg: Message) => Message) => {
    setSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, messages: s.messages.map(m => m.id === msgId ? updater(m) : m) }
        : s
    ));
  }, []);

  const createNewSession = () => {
    const s = makeSession({ characterId });
    setSessions(prev => [s, ...prev]);
    setActiveId(s.id);
    setMedia([]);
  };

  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions(prev => {
      const next = prev.filter(s => s.id !== id);
      if (next.length === 0) {
        const fresh = makeSession({ characterId });
        setActiveId(fresh.id);
        return [fresh];
      }
      if (id === activeId) setActiveId(next[0].id);
      return next;
    });
  };

  const switchSession = async (id: string) => {
    if (id === activeId || isLoading) return;
    setActiveId(id);
    setMedia([]);

    const targetSession = sessions.find(s => s.id === id);
    if (targetSession && !targetSession.id.startsWith('sess_') && !targetSession.isLoaded && sessionToken) {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/chat/sessions/${id}`, {
          headers: { 'Authorization': `Bearer ${sessionToken}` }
        });
        const json = await res.json();
        if (json.messages) {
          updateSession(id, s => ({ ...s, messages: json.messages, isLoaded: true }));
        }
      } catch (e) {
        console.error('Failed to load session history', e);
      }
    }
  };

  const setMode = (m: ChatMode) =>
    updateSession(activeId, s => ({ ...s, mode: m }));

  const setCharacterId = (cid: CharacterId) =>
    updateSession(activeId, s => ({ ...s, characterId: cid }));

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => setMedia(prev => [...prev, reader.result as string]);
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const removeMedia = (index: number) => setMedia(prev => prev.filter((_, i) => i !== index));

  const handleImageUpload = (file: File) => {
    const reader = new FileReader();
    reader.onloadend = () => setMedia(prev => [...prev, reader.result as string]);
    reader.readAsDataURL(file);
  };

  // Convert Profile to context string
  const getProfileContextString = () => {
    if (!userProfile) return '';
    return `User Profile Context => ID/Name: ${userProfile.username}, Gender: ${userProfile.gender}, Status: ${userProfile.relationship_status}, Age: ${userProfile.age || 'N/A'}, Occupation: ${userProfile.occupation || 'N/A'}, MBTI: ${userProfile.mbti || 'N/A'}, Ideal Type: ${userProfile.ideal_type || 'N/A'}, Current Challenge: ${userProfile.current_challenge || 'N/A'}, Goal from AI: ${userProfile.wingman_goal || 'N/A'}, Red Flags/Deal Breakers: ${userProfile.deal_breakers || 'N/A'}`;
  };

  const handleSend = async (inputText: string) => {
    if ((!inputText.trim() && media.length === 0) || isLoading || !activeSession) return;

    if (forceSetup) {
      setShowProfileModal(true);
      return;
    }

    const capturedSessionId = activeId;
    const capturedMode = activeSession.mode;
    const capturedCharacter = activeSession.characterId;
    const userText = inputText;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userText,
      media: media.length > 0 ? media : undefined,
      timestamp: new Date(),
    };

    const assistantId = (Date.now() + 1).toString();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isThinking: true,
      toolSteps: [],
      isDone: false,
      timestamp: new Date(),
    };

    setSessions(prev => prev.map(s => {
      if (s.id !== capturedSessionId) return s;
      const isFirstUserMsg = s.messages.filter(m => m.role === 'user').length === 0;
      return {
        ...s,
        title: isFirstUserMsg ? userText.slice(0, 30) || 'New Session' : s.title,
        messages: [...s.messages, userMsg, assistantMsg],
      };
    }));

    setMedia([]);
    setIsLoading(true);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      };
      if (sessionToken) {
        headers['Authorization'] = `Bearer ${sessionToken}`;
      }

      // Appending profile context implicitly via the prompt context field or just prepending it if backend doesn't take context param
      // Actually backend accepts "context" according to some typical designs, or we can just prepend it. Let's add it to the body request as profile_context.
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          chat_id: capturedSessionId,
          message: userText,
          mode: capturedMode,
          guest: false,
          quadrant: capturedCharacter,
          media: media.length > 0 ? media : undefined,
          profile_context: getProfileContextString()
        }),
      });

      if (!res.body) throw new Error('No response body');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let contentAccum = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\r\n\r\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;
          const lines = part.split('\n');
          let eventType = 'message';
          let data = '';
          for (const line of lines) {
            if (line.startsWith('event: ')) eventType = line.slice(7).trim();
            else if (line.startsWith('data: ')) data = line.slice(6).trim();
          }
          if (!data) continue;

          try {
            const payload = JSON.parse(data);
            const upd = (fn: (m: Message) => Message) =>
              updateAssistant(capturedSessionId, assistantId, fn);

            switch (eventType) {
              case 'skill_activated':
                upd(m => ({ ...m, activatedSkills: payload.skill_names || [], isThinking: true }));
                break;
              case 'step_announce':
                upd(m => ({ ...m, currentStep: payload.content || '', isThinking: false }));
                break;
              case 'reply_options':
                upd(m => ({
                  ...m,
                  replyOptions: payload.options || [],
                  replyAnalysis: payload.analysis || '',
                  isThinking: false,
                }));
                break;
              case 'subagent_spawned':
                upd(m => ({
                  ...m,
                  subagentSpawned: [...(m.subagentSpawned || []), { id: payload.task_id, task: payload.task }],
                  isThinking: true,
                  crewTasks: (m.crewTasks || []).map(t =>
                    t.subject && payload.task?.includes(t.subject) ? { ...t, status: 'running' as const } : t
                  ),
                }));
                break;
              case 'subagent_done':
                upd(m => ({
                  ...m,
                  crewTasks: (m.crewTasks || []).map(t =>
                    t.subject && payload.label?.includes(t.subject) ? { ...t, status: 'done' as const } : t
                  ),
                }));
                break;
              case 'crew_phase':
                upd(m => ({ ...m, crewPhase: payload.phase || 'plan', isThinking: payload.phase !== 'done' }));
                break;
              case 'crew_plan':
                upd(m => ({
                  ...m,
                  crewTasks: (payload.tasks || []).map((t: { id: number; subject: string; status: string }) => ({
                    id: t.id, subject: t.subject, status: 'pending' as const,
                  })),
                  crewPlanSummary: payload.plan_summary || '',
                  crewPhase: 'dispatch' as const,
                  isThinking: false,
                }));
                break;
              case 'thoughts':
                upd(m => ({ ...m, thoughts: payload.thoughts || [], currentStep: undefined }));
                break;
              case 'thinking':
                upd(m => ({ ...m, thinking: payload.content || '', isThinking: true }));
                break;
              case 'tool_start':
                upd(m => ({ 
                  ...m, 
                  isThinking: false, 
                  toolSteps: [...(m.toolSteps || []), { 
                    id: `${payload.tool_name}-${Date.now()}-${Math.random()}`, 
                    toolName: payload.tool_name, 
                    status: 'running' as ToolStepStatus, 
                    args: payload.tool_args 
                  }] 
                }));
                break;
              case 'tool_done':
                upd(m => ({ 
                  ...m, 
                  toolSteps: (m.toolSteps || []).map(step => 
                    step.toolName === payload.tool_name && step.status === 'running' 
                      ? { ...step, status: (payload.success ? 'success' : 'error') as ToolStepStatus } 
                      : step
                  ) 
                }));
                break;
              case 'progress':
                if (payload.content) {
                  if (contentAccum && !contentAccum.endsWith('\n\n') && !contentAccum.endsWith('\n')) {
                    contentAccum += '\n\n';
                  }
                  contentAccum += payload.content;
                }
                upd(m => ({ 
                  ...m, 
                  content: contentAccum, 
                  isThinking: false, 
                  crewPhase: m.crewPhase ? 'done' as const : undefined 
                }));
                break;
              case 'done':
                if (payload.content) {
                  if (contentAccum && !contentAccum.endsWith('\n\n') && !contentAccum.endsWith('\n')) {
                    contentAccum += '\n\n';
                  }
                  contentAccum += payload.content;
                }
                upd(m => ({ 
                  ...m, 
                  content: contentAccum, 
                  isThinking: false, 
                  isDone: true, 
                  crewPhase: m.crewPhase ? 'done' as const : undefined 
                }));
                break;
              case 'error':
                upd(m => ({ 
                  ...m, 
                  content: `⚠️ Error: ${payload.error || 'Unknown error'}`, 
                  isThinking: false, 
                  isDone: true 
                }));
                break;
            }
          } catch (err) {
            console.error('Failed to parse SSE data:', err, data);
          }
        }
      }

      updateAssistant(capturedSessionId, assistantId, m => ({ 
        ...m, 
        isDone: true, 
        isThinking: false,
        timestamp: new Date()
      }));
    } catch (error) {
      console.error('Chat error:', error);
      updateAssistant(capturedSessionId, assistantId, m => ({
        ...m, 
        content: '⚠️ Network error, please check if the backend service is running.', 
        isThinking: false, 
        isDone: true,
        timestamp: new Date()
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const chatSessions: ChatSession[] = sessions.map(s => ({
    id: s.id,
    title: s.title,
    createdAt: s.createdAt,
  }));

  const isAnyThinking = messages.some(m => m.role === 'assistant' && m.isThinking);

  return (
    <>
      <div className="h-screen flex bg-cyber-black text-white overflow-hidden">
        {/* Sidebar */}
        <ChatSidebar 
          characterName={character.name}
          characterTitle={character.title}
          characterColor={character.color}
          onNewSession={createNewSession}
          sessions={chatSessions}
          activeSessionId={activeId}
          onSwitchSession={switchSession}
          onDeleteSession={deleteSession}
          onOpenSettings={() => setShowProfileModal(true)}
        />

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col relative">
          {/* Grid Background */}
          <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />
          
          {/* Header */}
          <ChatHeader
            characterName={character.name}
            characterTitle={character.title}
            characterColor={character.color}
            protocolName={character.protocol}
          />

          {messages.length === 0 && (
            <div className="flex-shrink-0 py-8 px-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center"
              >
                <div className="relative mb-4">
                  <div className={`
                    absolute inset-0 rounded-full blur-2xl opacity-30 animate-pulse
                    ${character.color === 'cyan' ? 'bg-cyber-cyan' : 
                      character.color === 'amber' ? 'bg-cyber-amber' : 
                      character.color === 'purple' ? 'bg-cyber-purple' : 'bg-cyber-pink'}
                  `} />
                  <div className={`
                    relative w-24 h-24 rounded-full overflow-hidden border-2
                    ${character.color === 'cyan' ? 'border-cyber-cyan shadow-glow-cyan' : 
                      character.color === 'amber' ? 'border-cyber-amber shadow-glow-amber' : 
                      character.color === 'purple' ? 'border-cyber-purple shadow-glow-purple' : 'border-cyber-pink shadow-glow-pink'}
                  `}>
                    <img 
                      src={character.image} 
                      alt={character.name}
                      className="w-full h-full object-cover object-top"
                    />
                  </div>
                </div>

                <h2 className={`text-2xl font-black italic ${
                  character.color === 'cyan' ? 'text-cyber-cyan' : 
                  character.color === 'amber' ? 'text-cyber-amber' : 
                  character.color === 'purple' ? 'text-cyber-purple' : 'text-cyber-pink'
                }`}>
                  {character.name.toUpperCase()}
                </h2>
                <p className="text-[10px] tracking-[0.3em] text-neutral-03 uppercase mb-4">
                  {character.title}
                </p>

                <div className="flex gap-2">
                  {character.traits.map((trait, i) => (
                    <span 
                      key={i}
                      className={`
                        px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest
                        border ${
                          character.color === 'cyan' ? 'border-cyber-cyan/30 text-cyber-cyan/80' : 
                          character.color === 'amber' ? 'border-cyber-amber/30 text-cyber-amber/80' : 
                          character.color === 'purple' ? 'border-cyber-purple/30 text-cyber-purple/80' : 
                          'border-cyber-pink/30 text-cyber-pink/80'
                        } bg-white/[0.02]
                      `}
                    >
                      {trait}
                    </span>
                  ))}
                </div>
              </motion.div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto px-4 lg:px-8 pb-4">
            <div className="max-w-3xl mx-auto space-y-6">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    characterImage={character.image}
                    characterColor={character.color}
                    characterName={character.name}
                    mode={mode}
                  />
                ))}
              </AnimatePresence>
              
              {isAnyThinking && (
                <TypingIndicator 
                  characterColor={character.color}
                  text={
                    character.id === 'aphrodite' ? "Analyzing the tea..." :
                    character.id === 'chiron' ? "Calculating optimal strategy..." :
                    character.id === 'odysseus' ? "Evaluating the situation..." :
                    "Assessing power dynamics..."
                  }
                />
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="flex-shrink-0">
            <ChatInput
              onSend={handleSend}
              onImageUpload={handleImageUpload}
              characterColor={character.color}
              placeholder={
                character.id === 'aphrodite' 
                  ? "Paste a screenshot or tell me what's going on..." :
                character.id === 'chiron'
                  ? "Describe your situation or upload a conversation..." :
                character.id === 'odysseus'
                  ? "Share what's happening in your relationship..." :
                  "Tell me about the power dynamics at play..."
              }
              disabled={isLoading}
              mode={mode}
              onModeChange={setMode}
              media={media}
              onRemoveMedia={removeMedia}
            />
          </div>

          <div className="text-center py-3">
            <p className="text-[8px] tracking-[0.4em] font-mono text-neutral-04 uppercase">
              {character.name.toUpperCase()} AI 2.0 // Decrypting Emotion in Real-Time
            </p>
          </div>
        </main>
      </div>

      <ProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        sessionToken={sessionToken || ''}
        userId={userId || ''}
        forceMandatory={forceSetup}
        onProfileUpdated={() => {
            const supabase = createSupabaseBrowserClient();
            if (userId) fetchProfile(supabase, userId);
            setShowProfileModal(false);
        }}
      />
    </>
  );
}
