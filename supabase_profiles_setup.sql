-- 1. Create the `profiles` table
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL PRIMARY KEY,
  username TEXT NOT NULL,
  gender TEXT NOT NULL,
  relationship_status TEXT NOT NULL,
  
  -- Optional extended profile fields
  age TEXT,
  occupation TEXT,
  religion TEXT,
  social_media TEXT,
  financial_status TEXT,
  mbti TEXT,
  core_personality TEXT,
  ideal_type TEXT,
  current_challenge TEXT,
  wingman_goal TEXT,
  deal_breakers TEXT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. Create policies
-- Users can view their own profile
CREATE POLICY "Users can view own profile" 
  ON public.profiles 
  FOR SELECT 
  USING (auth.uid() = id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile" 
  ON public.profiles 
  FOR INSERT 
  WITH CHECK (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" 
  ON public.profiles 
  FOR UPDATE 
  USING (auth.uid() = id) 
  WITH CHECK (auth.uid() = id);

-- (Optional but recommended) Automatically create a profile stub when a user signs up.
-- We won't block signups if this fails, but it helps ensure a row exists.
-- You can handle the "first time login form" strictly in the frontend.
