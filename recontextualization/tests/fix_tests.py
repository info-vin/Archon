import glob
import os
import re

def fix_test_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    modified = False
    
    for line in lines:
        if 'Engine.register_singleton(' in line and 'if Engine.has_singleton' not in '\n'.join(new_lines[-2:]):
            match = re.search(r'Engine\.register_singleton\("([^"]+)"', line)
            if match:
                singleton_name = match.group(1)
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f'{indent}if Engine.has_singleton("{singleton_name}"):')
                # Check indentation style (tabs vs spaces)
                if '\t' in indent or not indent:
                    new_lines.append(f'{indent}\tEngine.unregister_singleton("{singleton_name}")')
                else:
                    new_lines.append(f'{indent}    Engine.unregister_singleton("{singleton_name}")')
                modified = True
        new_lines.append(line)

    if modified:
        with open(filepath, 'w') as f:
            f.write('\n'.join(new_lines))
        print(f"Fixed {filepath}")

for f in glob.glob('recontextualization/tests/*.gd'):
    fix_test_file(f)
