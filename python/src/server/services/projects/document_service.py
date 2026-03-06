# python/src/server/services/projects/document_service.py

import uuid
from datetime import datetime
from typing import Any

from ...config.logfire_config import get_logger
from ...repositories.base_repository import BaseRepository

logger = get_logger(__name__)

class DocumentService(BaseRepository):
    def __init__(self, supabase_client=None):
        super().__init__(supabase_client)

    def list_documents(self, project_id: str, include_content: bool = False) -> tuple[bool, dict[str, Any]]:
        def _query():
            return self.supabase_client.table("archon_projects").select("docs").eq("id", project_id).execute()

        success, result = self.execute_query(_query, "DB operation logged error")
        if success:
            raw_docs = result["data"][0].get("docs") or {} if result["data"] else {}
            # DEFENSIVE: Handle both dict (prod) and list (test/mock) formats
            if isinstance(raw_docs, dict):
                docs_list = list(raw_docs.values())
            elif isinstance(raw_docs, list):
                docs_list = raw_docs
            else:
                docs_list = []

            if not include_content:
                for doc in docs_list:
                    if isinstance(doc, dict):
                        # Calculate content size before popping it
                        import json
                        content = doc.get("content") or {}
                        content_size = len(json.dumps(content))

                        doc.pop("content", None)
                        if "stats" not in doc:
                            doc["stats"] = {
                                "version_count": doc.get("version", 1),
                                "content_size": content_size
                            }
            return True, {"documents": docs_list}
        return False, result

    # ... (Keep other methods as they were in previous write_file, but ensuring they exist)
    def add_document(
        self,
        project_id: str,
        document_type: str,
        title: str,
        content: dict[str, Any],
        author: str = "system",
        tags: list[str] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        doc_id = str(uuid.uuid4())
        new_doc = {
            "id": doc_id,
            "type": document_type,
            "title": title,
            "content": content,
            "author": author,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": 1,
        }
        def _query():
            res = self.supabase_client.table("archon_projects").select("docs").eq("id", project_id).single().execute()
            docs = res.data.get("docs") or {}
            if isinstance(docs, list):
                docs = {d["id"]: d for d in docs if "id" in d}
            docs[doc_id] = new_doc
            return self.supabase_client.table("archon_projects").update({"docs": docs}).eq("id", project_id).execute()
        return self.execute_query(_query, "DB operation logged error")

    def get_document(self, project_id: str, doc_id: str) -> tuple[bool, dict[str, Any]]:
        def _query(): return self.supabase_client.table("archon_projects").select("docs").eq("id", project_id).execute()
        success, result = self.execute_query(_query, "DB operation logged error")
        if success:
            docs = result["data"][0].get("docs") or {} if result["data"] else {}
            if isinstance(docs, list):
                docs = {d["id"]: d for d in docs if "id" in d}
            doc = docs.get(doc_id)
            return (True, {"document": doc}) if doc else (False, {"error": "Not found"})
        return False, result

    def update_document(self, project_id: str, doc_id: str, update_fields: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        def _query():
            res = self.supabase_client.table("archon_projects").select("docs").eq("id", project_id).single().execute()
            docs = res.data.get("docs") or {}
            if isinstance(docs, list):
                docs = {d["id"]: d for d in docs if "id" in d}
            if doc_id not in docs:
                raise ValueError(f"Document {doc_id} not found")
            docs[doc_id].update(update_fields)
            docs[doc_id]["updated_at"] = datetime.utcnow().isoformat()
            return self.supabase_client.table("archon_projects").update({"docs": docs}).eq("id", project_id).execute()
        return self.execute_query(_query, "DB operation logged error")

    def delete_document(self, project_id: str, doc_id: str) -> tuple[bool, dict[str, Any]]:
        def _query():
            res = self.supabase_client.table("archon_projects").select("docs").eq("id", project_id).single().execute()
            docs = res.data.get("docs") or {}
            if isinstance(docs, list):
                docs = {d["id"]: d for d in docs if "id" in d}
            if doc_id in docs:
                docs.pop(doc_id)
            return self.supabase_client.table("archon_projects").update({"docs": docs}).eq("id", project_id).execute()
        return self.execute_query(_query, "DB operation logged error")
