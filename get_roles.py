import asyncio
from src.server.utils import get_supabase_client
def main():
    supabase = get_supabase_client()
    result = supabase.table("archon_roles_permissions").select("*").execute()
    for row in result.data:
        print(row['role'], row['permissions'])
main()
