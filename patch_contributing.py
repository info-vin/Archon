with open('CONTRIBUTING_tw.md', 'r') as f:
    content = f.read()

search = """- `migration/20260810_seed_rag_blog.sql`"""
replace = """- `migration/20260810_seed_rag_blog.sql`
- `migration/20260815_seed_insight_report_blog.sql`
- `migration/20260819_add_hybrid_router_settings.sql`
- `migration/20260819_update_rag_threshold.sql`
- `migration/20260821_update_leads_patrol_prompt.sql`"""

if search in content and replace not in content:
    content = content.replace(search, replace)
    with open('CONTRIBUTING_tw.md', 'w') as f:
        f.write(content)
