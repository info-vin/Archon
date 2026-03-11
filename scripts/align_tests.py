import os
import re

def align_test_paths(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rule: Point patches to the actual sub-module instead of the facade
    new_content = re.sub(r'patch\(["\']server\.api_routes\.knowledge_api\.RBACService["\']', 
                         'patch(\"server.api_routes.knowledge.items.RBACService\"', content)
    
    new_content = re.sub(r'patch\(["\']server\.api_routes\.knowledge_api\.extract_text_from_document["\']', 
                         'patch(\"server.api_routes.knowledge.upload.extract_text_from_document\"', new_content)

    new_content = re.sub(r'patch\(["\']server\.api_routes\.knowledge_api\.DocumentStorageService["\']', 
                         'patch(\"server.api_routes.knowledge.upload.DocumentStorageService\"', new_content)

    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

targets = [
    'python/tests/server/api_routes/test_knowledge_api_security.py',
    'python/tests/test_file_upload_integration.py'
]

for t in targets:
    if os.path.exists(t):
        if align_test_paths(t):
            print(f"Aligned {t} to real paths.")
