import re

with open("python/src/server/services/propose_change_service.py", "r") as f:
    content = f.read()

# Add import if not exists
if "from ..repositories.base_repository import BaseRepository" not in content:
    content = content.replace("from typing import Any, cast", "from typing import Any, cast\nfrom ..repositories.base_repository import BaseRepository")

# Change class definition
content = content.replace(
    "class ProposeChangeService:",
    "class ProposeChangeService(BaseRepository):"
)

content = content.replace(
    "    def __init__(self, db_client: Client | None = None) -> None:\n        self.db_client = db_client or get_supabase_client()",
    "    def __init__(self, db_client: Client | None = None) -> None:\n        super().__init__(db_client)\n        self.db_client = self.supabase_client"
)

# 1. list_proposals
list_old = """        query = query.order("created_at", desc=True)
        response = query.execute()

        return cast(list[ProposedChangeDict], response.data)"""
list_new = """        query = query.order("created_at", desc=True)
        success, response = self.execute_query(query, "Failed to list proposals")

        return cast(list[ProposedChangeDict], response.get("data", []) if success else [])"""
content = content.replace(list_old, list_new)

list_prof_old = """                p_res = self.db_client.table("profiles").select("department, role").eq("id", user_str).execute() # 合法
                if p_res.data and len(p_res.data) > 0:
                    profile = p_res.data[0]"""
list_prof_new = """                p_success, p_res = self.execute_query(self.db_client.table("profiles").select("department, role").eq("id", user_str), "Fetch profile")
                if p_success and p_res.get("data") and len(p_res["data"]) > 0:
                    profile = p_res["data"][0]"""
content = content.replace(list_prof_old, list_prof_new)

# 2. get_proposal
get_old = """    async def get_proposal(self, proposal_id: UUID) -> ProposedChangeDict | None:
        response = self.db_client.table("proposed_changes").select("*").eq("id", str(proposal_id)).execute()
        if not response.data:
            return None
        return cast(ProposedChangeDict, response.data[0])"""
get_new = """    async def get_proposal(self, proposal_id: UUID) -> ProposedChangeDict | None:
        success, response = self.execute_query(self.db_client.table("proposed_changes").select("*").eq("id", str(proposal_id)), "Get proposal")
        if not success or not response.get("data"):
            return None
        return cast(ProposedChangeDict, response["data"][0])"""
content = content.replace(get_old, get_new)

# 3. create_file_proposal
create_file_old = """            try:
                u_res = self.db_client.table("profiles").select("department").eq("id", user_str).execute()
                if u_res.data:
                    dept = u_res.data[0].get("department", "General")
            except Exception:
                pass"""
create_file_new = """            try:
                s, u_res = self.execute_query(self.db_client.table("profiles").select("department").eq("id", user_str), "Get user dept")
                if s and u_res.get("data"):
                    dept = u_res["data"][0].get("department", "General")
            except Exception:
                pass"""
content = content.replace(create_file_old, create_file_new)

# 4. create_proposal
create_old = """            try:
                u_res = self.db_client.table("profiles").select("department").eq("id", user_id).execute()
                if u_res.data:
                    dept = u_res.data[0].get("department", "General")
            except Exception:
                pass"""
create_new = """            try:
                s, u_res = self.execute_query(self.db_client.table("profiles").select("department").eq("id", user_id), "Get user dept")
                if s and u_res.get("data"):
                    dept = u_res["data"][0].get("department", "General")
            except Exception:
                pass"""
content = content.replace(create_old, create_new)

create_insert_old = """        response = self.db_client.table("proposed_changes").insert(data).execute()
        if not response.data:
            raise RuntimeError("Failed to insert proposal")

        self.logger.info(f"Created proposal {response.data[0].get('id')} of type {change_type}")
        return cast(ProposedChangeDict, response.data[0])"""
create_insert_new = """        success, response = self.execute_query(self.db_client.table("proposed_changes").insert(data), "Insert proposal")
        if not success or not response.get("data"):
            raise RuntimeError("Failed to insert proposal")

        self.logger.info(f"Created proposal {response['data'][0].get('id')} of type {change_type}")
        return cast(ProposedChangeDict, response["data"][0])"""
content = content.replace(create_insert_old, create_insert_new)

# 5. approve_proposal
approve_update_old = """        response = self.db_client.table("proposed_changes").update(success_data).eq("id", str(proposal_id)).execute()

        # 3. Execute
        if response.data:
            proposal_data = response.data[0]"""
approve_update_new = """        success, response = self.execute_query(self.db_client.table("proposed_changes").update(success_data).eq("id", str(proposal_id)), "Approve proposal")

        # 3. Execute
        if success and response.get("data"):
            proposal_data = response["data"][0]"""
content = content.replace(approve_update_old, approve_update_new)

approve_audit_old = """            if user_str:
                u_res = self.db_client.table("profiles").select("name").eq("id", str(user_str)).execute()
                if u_res.data:
                    user_name = u_res.data[0].get("name", "Unknown Admin")"""
approve_audit_new = """            if user_str:
                s, u_res = self.execute_query(self.db_client.table("profiles").select("name").eq("id", str(user_str)), "Get user name")
                if s and u_res.get("data"):
                    user_name = u_res["data"][0].get("name", "Unknown Admin")"""
content = content.replace(approve_audit_old, approve_audit_new)

approve_ret_old = """        self.logger.info(f"Proposal {proposal_id} approved by {user_str}")
        return cast(ProposedChangeDict, response.data[0])"""
approve_ret_new = """        self.logger.info(f"Proposal {proposal_id} approved by {user_str}")
        return cast(ProposedChangeDict, response["data"][0])"""
content = content.replace(approve_ret_old, approve_ret_new)

# 6. reject_proposal
reject_update_old = """        response = self.db_client.table("proposed_changes").update(data).eq("id", str(proposal_id)).execute()
        if not response.data:
            raise RuntimeError(f"Failed to reject proposal {proposal_id}")"""
reject_update_new = """        success, response = self.execute_query(self.db_client.table("proposed_changes").update(data).eq("id", str(proposal_id)), "Reject proposal")
        if not success or not response.get("data"):
            raise RuntimeError(f"Failed to reject proposal {proposal_id}")"""
content = content.replace(reject_update_old, reject_update_new)

reject_audit_old = """            if user_str:
                u_res = self.db_client.table("profiles").select("name").eq("id", str(user_str)).execute()
                if u_res.data:
                    user_name = u_res.data[0].get("name", "Unknown Admin")"""
reject_audit_new = """            if user_str:
                s, u_res = self.execute_query(self.db_client.table("profiles").select("name").eq("id", str(user_str)), "Get user name")
                if s and u_res.get("data"):
                    user_name = u_res["data"][0].get("name", "Unknown Admin")"""
content = content.replace(reject_audit_old, reject_audit_new)

reject_ret_old = """        self.logger.info(f"Proposal {proposal_id} rejected by {user_str}")
        return cast(ProposedChangeDict, response.data[0])"""
reject_ret_new = """        self.logger.info(f"Proposal {proposal_id} rejected by {user_str}")
        return cast(ProposedChangeDict, response["data"][0])"""
content = content.replace(reject_ret_old, reject_ret_new)


with open("python/src/server/services/propose_change_service.py", "w") as f:
    f.write(content)
