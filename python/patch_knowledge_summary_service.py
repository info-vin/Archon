import sys

filepath = 'python/src/server/services/knowledge/knowledge_summary_service.py'
with open(filepath, 'r') as f:
    content = f.read()

new_method = """
    async def get_item_chunks(self, source_id: str, page: int = 1, per_page: int = 50, domain_filter: str | None = None) -> tuple[bool, dict[str, Any]]:
        \"\"\"
        Get document chunks for a specific knowledge item with pagination and optional domain filtering.
        \"\"\"
        try:
            safe_logfire_info(f"Fetching chunks for source_id: {source_id}, page={page}, per_page={per_page}, domain_filter={domain_filter}")

            query = self.supabase.from_("archon_crawled_pages").select(
                "id, source_id, content, metadata, url", count="exact"
            )
            query = query.eq("source_id", source_id)

            if domain_filter:
                query = query.ilike("url", f"%{domain_filter}%")

            offset = (page - 1) * per_page

            # Deterministic ordering
            query = query.order("url", desc=False).order("id", desc=False)

            # Apply pagination
            query = query.range(offset, offset + per_page - 1)

            result = query.execute()

            if getattr(result, "error", None):
                safe_logfire_error(f"Supabase query error | source_id={source_id} | error={result.error}")
                return False, {"error": str(result.error)}

            chunks = result.data if result.data else []
            total_count = result.count if hasattr(result, "count") and result.count is not None else len(chunks)

            return True, {
                "chunks": chunks,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total_count + per_page - 1) // per_page if total_count > 0 else 0
                }
            }
        except Exception as e:
            safe_logfire_error(f"Failed to fetch chunks | source_id={source_id} | error={str(e)}")
            return False, {"error": str(e)}
"""

if "def get_item_chunks" not in content:
    content = content + new_method
    with open(filepath, 'w') as f:
        f.write(content)
    print("Method added.")
else:
    print("Method already exists.")
