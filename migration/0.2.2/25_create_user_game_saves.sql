-- Migration: Create user_game_saves table for Archon Agency Tycoon cloud saves
-- Category: Business / Games

CREATE TABLE IF NOT EXISTS public.user_game_saves (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    save_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Owner assignment
ALTER TABLE public.user_game_saves OWNER TO postgres;

-- Enable Row Level Security (RLS)
ALTER TABLE public.user_game_saves ENABLE ROW LEVEL SECURITY;

-- Grants
GRANT ALL ON TABLE public.user_game_saves TO authenticated;
GRANT ALL ON TABLE public.user_game_saves TO service_role;

-- RLS Policies
DROP POLICY IF EXISTS "Users can manage their own game saves" ON public.user_game_saves;
CREATE POLICY "Users can manage their own game saves" 
    ON public.user_game_saves 
    FOR ALL 
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Description comment
COMMENT ON TABLE public.user_game_saves IS 'Stores serialized tycoon game progress for authenticated users.';
