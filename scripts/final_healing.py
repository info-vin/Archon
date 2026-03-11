import os
import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rule 1: Change all 'from ...' or 'from ..' to 'from server.'
    # EXCEPT in main.py which needs to be relative
    if 'main.py' in file_path:
        return False
        
    new_content = re.sub(r'from \.\.\.\.', 'from server.', content)
    new_content = re.sub(r'from \.\.\.', 'from server.', new_content)
    new_content = re.sub(r'from \.\.', 'from server.', new_content)
    # Special: some might be single dot from .xxx
    # We only change it if it's NOT a valid relative import (e.g., from . import xxx is fine)
    # Actually, to be safe, let's convert EVERYTHING to server.
    new_content = re.sub(r'from \.', 'from server.', new_content)
    
    # Fix double server.server
    new_content = re.sub(r'from server\.server\.', 'from server.', new_content)

    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

server_dir = 'python/src/server'
fixed = 0
for root, _, files in os.walk(server_dir):
    for file in files:
        if file.endswith('.py'):
            if fix_file(os.path.join(root, file)):
                fixed += 1
print(f"Final healing: Unified {fixed} files to absolute 'server.' imports.")
