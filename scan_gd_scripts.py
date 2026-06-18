import os
import re

def scan_files(directory):
    magic_number_pattern = re.compile(r'(?<![A-Za-z0-9_])([0-9]{2,})(?![A-Za-z0-9_])')
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.gd'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    for i, line in enumerate(f):
                        line = line.strip()
                        if line.startswith('const ') or line.startswith('var '): continue
                        if line.startswith('#'): continue
                        matches = magic_number_pattern.findall(line)
                        if matches:
                            print(f"{filepath}:{i+1}: {line}")

if __name__ == '__main__':
    scan_files('arena/Scripts')
