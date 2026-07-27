import os
import re

files_to_check = [
    "src/server/services/visit_log_service.py",
    "src/server/services/report_service.py",
    "src/server/services/propose_change_service.py",
    "src/server/services/blog_service.py",
    "src/server/services/projects/document_service.py",
    "src/server/services/projects/project_creation_service.py",
    "src/server/services/projects/project_service.py",
    "src/server/services/projects/task_service.py",
    "src/server/services/projects/versioning_service.py",
    "src/server/services/projects/tasks/query_logic.py",
    "src/server/services/projects/tasks/create_logic.py",
    "src/server/services/projects/tasks/maintenance.py",
    "src/server/services/projects/tasks/update_logic.py",
    "src/server/services/projects/tasks/ai_operations.py",
    "src/server/services/marketing/lead_handler.py",
    "src/server/services/marketing/sales_pitch.py",
    "src/server/services/marketing/blog_generator.py",
]

for file_path in files_to_check:
    full_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(full_path):
        continue
    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    # Replace def __init__(self, supabase_client=None): -> def __init__(self, supabase_client: Any | None = None) -> None:
    content = re.sub(
        r'def __init__\(\s*self\s*,\s*supabase_client\s*=\s*None\s*\)\s*:',
        r'def __init__(self, supabase_client: Any | None = None) -> None:',
        content
    )

    # We can also do a generic regex for 1-line _query:
    # def _query():\n    return self.supabase_client...execute()
    # success, res = self.execute_query(_query, ...)

    # Let's find simple ones
    pattern_simple = re.compile(
        r'([ \t]+)def _query\(\):\n\1[ \t]+return (.*?)\.execute\(\)\n\n\1(.*?)self\.execute_query\(_query,\s*(.*?)\)',
        re.DOTALL
    )

    while True:
        match = pattern_simple.search(content)
        if not match:
            break
        indent = match.group(1)
        query_expr = match.group(2)
        exec_prefix = match.group(3)
        exec_args = match.group(4)

        replacement = f"{indent}{exec_prefix}self.execute_query({query_expr}, {exec_args})"
        content = content[:match.start()] + replacement + content[match.end():]

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Simple DRY replacement complete.")
