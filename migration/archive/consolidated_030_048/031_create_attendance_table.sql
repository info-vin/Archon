-- 031_create_attendance_table.sql
-- Purpose: Add attendance tracking and visit types for Mobile/Field Ops (Phase 4.6.5)

-- 1. Create attendance_logs table
CREATE TABLE IF NOT EXISTS public.attendance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    clock_in_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    clock_out_time TIMESTAMPTZ,
    latitude FLOAT,
    longitude FLOAT,
    location_name TEXT,
    status TEXT NOT NULL CHECK (status IN ('PRESENT', 'AWAY', 'OFF_WORK', 'MOCK_PRESENT')), 
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_attendance_user_time ON public.attendance_logs(user_id, clock_in_time DESC);

-- 3. Add visit_type to visit_logs if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'visit_logs' AND column_name = 'visit_type') THEN
        ALTER TABLE public.visit_logs ADD COLUMN visit_type TEXT;
    END IF;
END $$;

-- 4. Enable RLS for attendance_logs
ALTER TABLE public.attendance_logs ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies for attendance_logs
-- Users can view their own logs
DROP POLICY IF EXISTS "Users can view own attendance" ON public.attendance_logs;
CREATE POLICY "Users can view own attendance" ON public.attendance_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Users can insert their own logs
DROP POLICY IF EXISTS "Users can insert own attendance" ON public.attendance_logs;
CREATE POLICY "Users can insert own attendance" ON public.attendance_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own logs (for clock out)
DROP POLICY IF EXISTS "Users can update own attendance" ON public.attendance_logs;
CREATE POLICY "Users can update own attendance" ON public.attendance_logs
    FOR UPDATE USING (auth.uid() = user_id);

-- Managers/Admins can view all logs (simplified for now, strictly enforced by backend logic mainly)
-- Ideally we check role, but strictly `auth.uid() = user_id` is safe for basic self-service.
-- Manager view policy can be added later if needed for reports.

-- 6. Register Migration
INSERT INTO public.schema_migrations (version) 
VALUES ('031_create_attendance_table') 
ON CONFLICT (version) DO NOTHING;
