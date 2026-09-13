-- Create index for is_recurring to prevent full table scans during Task Dispatcher background polling
CREATE INDEX IF NOT EXISTS idx_archon_tasks_is_recurring ON public.archon_tasks (is_recurring);

