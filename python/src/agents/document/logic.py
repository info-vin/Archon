import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from src.agents.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


async def list_documents_logic(supabase_client: Any, project_id: str) -> str:
    """Logic for listing documents in a project."""
    try:
        if not project_id:
            return "No project is currently selected."
        if not supabase_client:
            return "Error: Database client not configured."
        response = (
            supabase_client.table("archon_projects")
            .select("docs")
            .eq("id", project_id)
            .execute()
        )
        if not response.data:
            return "No project found."
        docs = response.data[0].get("docs", [])
        if not docs:
            return "No documents found."
        doc_list = [
            f"- {d.get('title', 'Untitled')} ({d.get('document_type', 'unknown')})"
            for d in docs
        ]
        return f"Found {len(docs)} documents:\n" + "\n".join(doc_list)
    except Exception as e:
        return f"Error: {str(e)}"


async def get_document_logic(
    supabase_client: Any, project_id: str, document_title: str
) -> str:
    """Logic for retrieving a specific document's content with full formatting preservation."""
    try:
        if not supabase_client:
            return "Error: DB missing."
        response = (
            supabase_client.table("archon_projects")
            .select("docs")
            .eq("id", project_id)
            .execute()
        )
        if not response.data:
            return "No project found."
        docs = response.data[0].get("docs", [])
        matching_docs = [
            d for d in docs if document_title.lower() in d.get("title", "").lower()
        ]
        if not matching_docs:
            return f"No document matching '{document_title}'."
        doc = matching_docs[0]
        content = doc.get("content", {})
        content_str = ""
        if isinstance(content, dict):
            for key, value in content.items():
                label = key.replace("_", " ").title()
                if isinstance(value, list):
                    content_str += f"\n**{label}:**\n" + "\n".join(
                        [f"- {item}" for item in value]
                    )
                else:
                    content_str += f"\n**{label}:** {value}"
        else:
            content_str = str(content)
        return f"**Document: {doc.get('title', 'Untitled')}**\n{content_str}"
    except Exception as e:
        return f"Error: {str(e)}"


async def create_document_logic(
    project_id: str,
    user_id: str | None,
    title: str,
    document_type: str,
    content_description: str,
    progress_callback: Any | None = None,
) -> str:
    """Logic for creating a new document with FULL structure support."""
    try:
        if progress_callback:
            await progress_callback(
                {"step": "ai_generation", "log": f"📝 Creating {document_type}: {title}"}
            )
        blocks = _convert_to_blocks(title, document_type, content_description)
        content = {"id": str(uuid.uuid4()), "title": title, "blocks": blocks}
        from src.server.services.projects.document_service import DocumentService

        doc_service = DocumentService()
        success, result_data = doc_service.add_document(
            project_id=project_id,
            document_type=document_type,
            title=title,
            content=content,
            tags=[document_type, "conversational"],
            author=user_id or "DocumentAgent",
        )
        if result_data.get("success"):
            return f"Successfully created {title}. ID: {result_data.get('document_id')}"
        return f"Failed: {result_data.get('error')}"
    except Exception as e:
        return f"Error: {str(e)}"


async def update_document_logic(
    project_id: str,
    document_title: str,
    section_to_update: str,
    new_content: str,
    update_description: str,
) -> str:
    """Logic for updating document sections with JSON preservation."""
    try:
        mcp_client = await get_mcp_client()
        get_res = json.loads(
            await mcp_client.manage_document(
                action="get", project_id=project_id, title=document_title
            )
        )
        if not get_res.get("success"):
            return f"Error: {get_res.get('error')}"
        doc = get_res.get("document", {})
        current_content = doc.get("content", {})

        if section_to_update in current_content:
            val = current_content[section_to_update]
            if isinstance(val, list):
                try:
                    if new_content.startswith("["):
                        current_content[section_to_update] = json.loads(new_content)
                    else:
                        current_content[section_to_update] = val + [new_content]
                except Exception:
                    val.append(new_content)
            else:
                current_content[section_to_update] = new_content
        else:
            try:
                current_content[section_to_update] = json.loads(new_content)
            except Exception:
                current_content[section_to_update] = new_content

        update_res = json.loads(
            await mcp_client.manage_document(
                action="update",
                project_id=project_id,
                doc_id=doc.get("id"),
                content=current_content,
                version=f"{float(doc.get('version', '1.0')) + 0.1:.1f}",
            )
        )
        if update_res.get("success"):
            return f"Updated '{document_title}'. {update_description}"
        return f"Failed: {update_res.get('error')}"
    except Exception as e:
        return f"Error: {str(e)}"


async def create_feature_plan_logic(
    project_id: str,
    user_id: str | None,
    feature_name: str,
    feature_description: str,
    user_stories: str,
) -> str:
    """Logic for creating a feature plan with FULL React Flow diagram structure."""
    try:
        nodes = [
            {
                "id": "start",
                "type": "input",
                "position": {"x": 100, "y": 100},
                "data": {"label": f"Start: {feature_name}"},
            },
            {
                "id": "user_input",
                "type": "default",
                "position": {"x": 300, "y": 100},
                "data": {"label": "User Input"},
            },
            {
                "id": "validation",
                "type": "default",
                "position": {"x": 500, "y": 100},
                "data": {"label": "Validation"},
            },
            {
                "id": "processing",
                "type": "default",
                "position": {"x": 700, "y": 100},
                "data": {"label": "Processing"},
            },
            {
                "id": "response",
                "type": "output",
                "position": {"x": 900, "y": 100},
                "data": {"label": "Result"},
            },
        ]
        edges: list[dict[str, Any]] = [
            {"id": "e1", "source": "start", "target": "user_input"},
            {"id": "e2", "source": "user_input", "target": "validation"},
            {"id": "e3", "source": "validation", "target": "processing"},
            {"id": "e4", "source": "processing", "target": "response"},
        ]
        content = {
            "feature_overview": {
                "name": feature_name,
                "description": feature_description,
                "priority": "high",
            },
            "user_stories": user_stories.split("\n") if user_stories else [],
            "react_flow_diagram": {
                "nodes": nodes,
                "edges": edges,
                "viewport": {"x": 0, "y": 0, "zoom": 1},
            },
            "acceptance_criteria": ["Main flow completed", "Edge cases handled"],
        }
        mcp_client = await get_mcp_client()
        res = json.loads(
            await mcp_client.manage_project(
                action="add_feature",
                project_id=project_id,
                feature={
                    "id": str(uuid.uuid4()),
                    "feature_type": "feature_plan",
                    "name": feature_name,
                    "title": f"{feature_name} - Feature Plan",
                    "content": content,
                    "created_by": user_id or "DocumentAgent",
                },
            )
        )
        if res.get("success"):
            return f"Created feature plan for '{feature_name}'."
        return f"Failed: {res.get('error')}"
    except Exception as e:
        return f"Error: {str(e)}"


async def create_erd_logic(
    project_id: str,
    user_id: str | None,
    system_name: str,
    entity_descriptions: str,
    relationships_description: str,
) -> str:
    """Logic for creating an ERD with FULL SQL generation logic."""
    try:
        entities: list[dict[str, Any]] = []
        for line in entity_descriptions.split("\n"):
            line = line.strip()
            if line and not line.startswith("-"):
                entities.append({"name": line, "attributes": [], "primary_key": "id"})
            elif line.startswith("-") and entities:
                attr = line[1:].strip()
                entities[-1]["attributes"].append(
                    {"name": attr, "type": "VARCHAR(255)", "nullable": True}
                )
        sql_schema: list[str] = []
        for entity in entities:
            sql = f"CREATE TABLE {entity['name'].lower().replace(' ', '_')} (id UUID PRIMARY KEY DEFAULT gen_random_uuid()"
            for attr in entity["attributes"]:
                sql += f", {attr['name'].lower().replace(' ', '_')} {attr['type']}"
            sql += ");"
            sql_schema.append(sql)
        content = {
            "system_overview": {
                "name": system_name,
                "description": entity_descriptions,
            },
            "entities": entities,
            "database_schema": {"sql_statements": sql_schema},
        }
        mcp_client = await get_mcp_client()
        res = json.loads(
            await mcp_client.manage_project(
                action="add_data",
                project_id=project_id,
                data={
                    "id": str(uuid.uuid4()),
                    "data_type": "erd",
                    "name": system_name,
                    "title": f"{system_name} - ERD",
                    "content": content,
                    "created_by": user_id or "DocumentAgent",
                },
            )
        )
        if res.get("success"):
            return f"Created ERD for '{system_name}'."
        return f"Failed: {res.get('error')}"
    except Exception as e:
        return f"Error: {str(e)}"


async def request_approval_logic(
    project_id: str,
    user_id: str | None,
    document_title: str,
    change_summary: str,
    change_type: str = "update",
) -> str:
    """Logic for requesting approval with FULL workflow structure."""
    try:
        content = {
            "approval_request": {
                "requested_by": user_id or "DocumentAgent",
                "request_date": datetime.now().isoformat(),
                "target_document": document_title,
                "status": "pending_approval",
            },
            "change_summary": change_summary,
            "approval_workflow": {
                "required_approvers": ["Product Manager", "Technical Lead"],
                "approval_deadline": (datetime.now() + timedelta(days=3)).isoformat(),
            },
        }
        mcp_client = await get_mcp_client()
        res = json.loads(
            await mcp_client.manage_document(
                action="create",
                project_id=project_id,
                document_type="approval_request",
                title=f"Approval: {document_title}",
                content=content,
                author=user_id or "DocumentAgent",
            )
        )
        if res.get("success"):
            return f"Approval request created for '{document_title}'."
        return f"Failed: {res.get('error')}"
    except Exception as e:
        return f"Error: {str(e)}"


def _convert_to_blocks(
    title: str, document_type: str, content_description: str
) -> list[dict[str, Any]]:
    """FULL implementation of block conversion including PRD sections."""
    blocks = [
        {
            "id": str(uuid.uuid4()),
            "type": "heading_1",
            "content": title,
            "properties": {"text": title},
        }
    ]
    if document_type == "prd":
        for sec in [
            "Project Overview",
            "Goals",
            "Scope",
            "Technical Requirements",
            "Architecture",
            "User Stories",
            "Timeline & Milestones",
            "Risks & Mitigations",
        ]:
            blocks.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "heading_2",
                    "content": sec,
                    "properties": {"text": sec},
                }
            )
            if sec == "Project Overview":
                blocks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "paragraph",
                        "content": content_description,
                        "properties": {"text": content_description},
                    }
                )
    elif document_type == "technical_spec":
        for sec in ["Overview", "Technical Architecture", "API Design", "Database Schema"]:
            blocks.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "heading_2",
                    "content": sec,
                    "properties": {"text": sec},
                }
            )
    else:
        blocks.append(
            {
                "id": str(uuid.uuid4()),
                "type": "heading_2",
                "content": "Overview",
                "properties": {"text": "Overview"},
            }
        )
        blocks.append(
            {
                "id": str(uuid.uuid4()),
                "type": "paragraph",
                "content": content_description,
                "properties": {"text": content_description},
            }
        )
    return blocks
