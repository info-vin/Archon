import time
import re

model_name_lower = "nomic-embed-text"

# Version 1: List recreation
def test_list():
    embedding_patterns = [
        'embed', 'embedding', 'bge-', 'e5-', 'sentence-', 'arctic-embed',
        'nomic-embed', 'mxbai-embed', 'snowflake-arctic-embed', 'gte-', 'stella-'
    ]
    return any(pattern in model_name_lower for pattern in embedding_patterns)

# Version 2: Precompiled regex
EMBEDDING_REGEX = re.compile(r'embed|embedding|bge-|e5-|sentence-|arctic-embed|nomic-embed|mxbai-embed|snowflake-arctic-embed|gte-|stella-')
def test_regex():
    return bool(EMBEDDING_REGEX.search(model_name_lower))

t0 = time.time()
for _ in range(100000):
    test_list()
print("List time:", time.time() - t0)

t0 = time.time()
for _ in range(100000):
    test_regex()
print("Regex time:", time.time() - t0)
