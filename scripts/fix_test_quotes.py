import os
import re

def fix_patch_quotes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix "server...' pattern (mismatched quotes)
    new_content = re.sub(r'patch\("server\.(.*?)\'', r'patch("server.\1"', content)
    # Fix 'server..." pattern (mismatched quotes)
    new_content = re.sub(r"patch\('server\.(.*?)'\"", r"patch('server.\1'", new_content)
    # Generic fix for any patch starting with " or ' but ending with the other
    new_content = re.sub(r'patch\("([^"]*?)\'', r'patch("\1"', new_content)
    new_content = re.sub(r"patch\('([^']*?)\"", r"patch('\1'", new_content)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

test_dir = 'python/tests'
fixed_count = 0
for root, _, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            if fix_patch_quotes(os.path.join(root, file)):
                fixed_count += 1

print(f"Fixed {fixed_count} files.")
