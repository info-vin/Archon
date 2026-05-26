
from src.server.core.db import get_supabase_client

sb = get_supabase_client()
res = sb.table("archon_embeddings").select("metadata").execute()
for r in res.data:
    m = r.get("metadata", {})
    s = m.get("source", "")
    if ".mp4" in s or ".webm" in s:
        print("Found video embedding:", s)
