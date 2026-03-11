import os
import re

def fix_imports_to_relative(file_path):
    root_dir = os.path.abspath('python/src')
    abs_file_path = os.path.abspath(file_path)
    rel_depth = abs_file_path.replace(root_dir, '').count(os.sep) - 1
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Prefix based on depth (e.g., if depth is 2, prefix is '..')
    # server/services/file.py (depth 2) -> from ..xxx
    # server/services/sub/file.py (depth 3) -> from ...xxx
    prefix = '.' * rel_depth
    if rel_depth == 0: prefix = '.'
    
    # Replace 'from server.' with relative prefix
    new_content = re.sub(r'from server\.', f'from {prefix}', content)
    # Special case for 'import server' which is rarely used but we fix it too
    new_content = re.sub(r'import server\.', f'import {prefix}', new_content)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

# Scan all python files in server
server_dir = 'python/src/server'
fixed_count = 0
for root, _, files in os.walk(server_dir):
    for file in files:
        if file.endswith('.py'):
            if fix_imports_to_relative(os.path.join(root, file)):
                fixed_count += 1

print(f"Self-healed {fixed_count} files with relative imports.")
