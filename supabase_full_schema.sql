-- =========================================================================
-- CYBER WINGMAN FULL SUPABASE DATABASE SCHEMA
-- This script sets up profiles, subscription plans, user sessions,
-- and chat messages. It also configures Row Level Security (RLS)
-- to ensure users can only access their own data.
-- =========================================================================

-- 1. Create Subscription Plans Table (Lookup Table)
CREATE TABLE IF NOT EXISTS public.subscription_plans (
    id TEXT PRIMARY KEY, -- e.g., 'free', 'pro', 'premium'
    name TEXT NOT NULL,
    monthly_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    features JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Insert default subscription plans
INSERT INTO public.subscription_plans (id, name, monthly_price, features)
VALUES 
    ('free', 'Free Tier', 0.00, '{"max_messages_per_month": 50, "features": ["Basic Chat"]}'::jsonb),
    ('pro', 'Pro Tier', 9.99, '{"max_messages_per_month": 1000, "features": ["Advanced Advice", "Image Analysis"]}'::jsonb),
    ('premium', 'Premium Tier', 29.99, '{"max_messages_per_month": 999999, "features": ["Unlimited", "Priority Processing"]}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 2. Create Expanded Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    -- Link to Supabase Auth user
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    
    -- New Auth/Account Metadata fields
    email TEXT,
    auth_provider TEXT,               -- e.g., 'google', 'email'
    credits INTEGER DEFAULT 50,       -- Starting credits for new users
    subscription_tier TEXT REFERENCES public.subscription_plans(id) DEFAULT 'free',
    
    -- Mandatory Profiling Info
    username TEXT,
    gender TEXT,
    relationship_status TEXT,

    -- Demographics & Lifestyle
    age TEXT,
    occupation TEXT,
    religion TEXT,
    social_media TEXT,
    financial_status TEXT,
    
    -- Psychological Profiling
    mbti TEXT,
    core_personality TEXT,
    ideal_type TEXT,
    current_challenge TEXT,
    deal_breakers TEXT,
    
    -- Wingman Settings
    wingman_goal TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Create Sessions Table
CREATE TABLE IF NOT EXISTS public.sessions (
    id TEXT PRIMARY KEY, -- UUID or custom ID (e.g. sess_...)
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT DEFAULT 'New Chat',
    quadrant TEXT DEFAULT 'tactical', -- 'tactical', 'strategist', 'bestie', 'advisor'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Create Messages Table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT REFERENCES public.sessions(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    
    role TEXT NOT NULL, -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb, -- Store tool_calls, skill_names, analysis, etc
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- =========================================================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- =========================================================================

ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- =========================================================================
-- CREATE SECURITY POLICIES
-- =========================================================================

-- Subscription Plans Policies (Everyone can read, only admin can write)
CREATE POLICY "Users can view subscription plans"
    ON public.subscription_plans FOR SELECT
    USING (true);

-- Profiles Policies
CREATE POLICY "Users can view their own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id) 
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" 
    ON public.profiles FOR INSERT 
    WITH CHECK (auth.uid() = id);

-- Sessions Policies
CREATE POLICY "Users can view their own sessions" 
    ON public.sessions FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" 
    ON public.sessions FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions" 
    ON public.sessions FOR UPDATE 
    USING (auth.uid() = user_id) 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own sessions" 
    ON public.sessions FOR DELETE 
    USING (auth.uid() = user_id);

-- Messages Policies
CREATE POLICY "Users can view their own session messages" 
    ON public.messages FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert messages to their own sessions" 
    ON public.messages FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own messages" 
    ON public.messages FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own messages" 
    ON public.messages FOR DELETE 
    USING (auth.uid() = user_id);

-- =========================================================================
-- AUTO-UPDATE UPDATED_AT TIMESTAMP
-- =========================================================================

-- Create a generic function to update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Attach triggers to relevant tables
DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

DROP TRIGGER IF EXISTS set_sessions_updated_at ON public.sessions;
CREATE TRIGGER set_sessions_updated_at
    BEFORE UPDATE ON public.sessions
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

-- =========================================================================
-- AUTO-CREATE PROFILE ON AUTH LOGIN/SIGNUP (Optional but recommended)
-- =========================================================================

-- Automatically create profile records when a new user signs up in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, auth_provider, credits, subscription_tier)
  VALUES (
      NEW.id, 
      NEW.email,
      NEW.raw_app_meta_data->>'provider',
      50,      -- Default starting credits
      'free'   -- Default tier
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Map trigger to auth tables
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
