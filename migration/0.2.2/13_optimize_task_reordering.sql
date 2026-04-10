-- migration/0.2.2/13_optimize_task_reordering.sql

-- 1. Create Stored Procedure for Atomic Task Reordering (N+1 Fix)
-- This increments task_order for all tasks in a project with a specific status
-- that have a task_order greater than or equal to the starting point.

CREATE OR REPLACE FUNCTION increment_task_orders(
    p_project_id UUID,
    p_status TEXT,
    p_start_order INT
)
RETURNS void AS $$
BEGIN
    UPDATE archon_tasks
    SET 
        task_order = task_order + 1,
        updated_at = NOW()
    WHERE 
        project_id = p_project_id 
        AND status = p_status
        AND task_order >= p_start_order;
END;
$$ LANGUAGE plpgsql;

-- 2. Register migration version
INSERT INTO schema_migrations (version) VALUES ('13_optimize_task_reordering') ON CONFLICT (version) DO NOTHING;
