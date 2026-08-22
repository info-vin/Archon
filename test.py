import re

with open('CONTRIBUTING_tw.md', 'r') as f:
    content = f.read()

print("- `migration/20260819_add_hybrid_router_settings.sql`" in content)
print("- `migration/0.2.3/01_schema_core.sql`" in content)
print("- `migration/20260810_seed_rag_blog.sql`" in content)
