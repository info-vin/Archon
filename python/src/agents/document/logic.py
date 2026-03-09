import json
import logging
import uuid
from datetime import datetime
from typing import Any

from src.agents.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


async def list_documents_logic(supabase_client: Any, project_id: str) -> str:
    """Logic for listing documents in a project."""
    try:
        if not project_id:
            return "No project is currently selected. Please specify a project or create one first to manage documents."

        if not supabase_client:
            return "Error: Database client not configured."

        response = (
            supabase_client.table("archon_projects")
            .select("docs")
            .eq("id", project_id)
            .execute()
        )

        if not response.data:
            return "No project found with the given ID."

        docs = response.data[0].get("docs", [])
        if not docs:
            return "No documents found in this project."

        doc_list = []
        for doc in docs:
            doc_type = doc.get("document_type", "unknown")
            title = doc.get("title", "Untitled")
            doc_list.append(f"- {title} ({doc_type})")

        return f"Found {len(docs)} documents:\n" + "\n".join(doc_list)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return f"Error retrieving documents: {str(e)}"


async def get_document_logic(
    supabase_client: Any, project_id: str, document_title: str
) -> str:
    """Logic for retrieving a specific document's content."""
    try:
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
        matching_docs = [
            doc for doc in docs if document_title.lower() in doc.get("title", "").lower()
        ]

        if not matching_docs:
            available_docs = [doc.get("title", "Untitled") for doc in docs[:5]]
            return f"No document found matching '{document_title}'. Available documents: {', '.join(available_docs)}"

        doc = matching_docs[0]
        content = doc.get("content", {})

        # Format content for display
        content_str = ""
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    content_str += f"\n**{key.replace('_', ' ').title()}:**\n" + "\n".join(
                        [f"- {item}" for item in value]
                    )
                elif isinstance(value, dict):
                    content_str += f"\n**{key.replace('_', ' ').title()}:**\n"
                    for subkey, subvalue in value.items():
                        content_str += f"  - {subkey}: {subvalue}\n"
                else:
                    content_str += f"\n**{key.replace('_', ' ').title()}:** {value}"
        else:
            content_str = str(content)

        return f"**Document: {doc.get('title', 'Untitled')}**\nType: {doc.get('document_type', 'unknown')}\nStatus: {doc.get('status', 'draft')}\nVersion: {doc.get('version', '1.0')}\n{content_str}"
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return f"Error retrieving document: {str(e)}"


async def create_document_logic(
    project_id: str,
    user_id: str | None,
    title: str,
    document_type: str,
    content_description: str,
    progress_callback: Any | None = None,
) -> str:
    """Logic for creating a new document with FULL Jules block logic."""
    try:
        if progress_callback:
            await progress_callback(
                {
                    "step": "ai_generation",
                    "log": f"📝 Creating {document_type}: {title}",
                }
            )

        # Generate blocks using the full implementation
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

        if result_data.get("success", False):
            doc_id = result_data.get("document_id", "unknown")
            if progress_callback:
                await progress_callback(
                    {
                        "step": "ai_generation",
                        "log": f"✅ Successfully created {document_type}: {title}",
                    }
                )
            return f"Successfully created document '{title}' of type '{document_type}'. Document ID: {doc_id}"
        else:
            error_msg = result_data.get("error", "Unknown error")
            if progress_callback:
                await progress_callback(
                    {
                        "step": "ai_generation",
                        "log": f"❌ Failed to create document: {error_msg}",
                    }
                )
            return f"Failed to create document: {error_msg}"
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        return f"Error creating document: {str(e)}"


async def update_document_logic(
    project_id: str,
    document_title: str,
    section_to_update: str,
    new_content: str,
    update_description: str,
) -> str:
    """Logic for updating an existing document."""
    try:
        mcp_client = await get_mcp_client()
        get_result = await mcp_client.manage_document(
            action="get", project_id=project_id, title=document_title
        )

        get_data = json.loads(get_result)
        if not get_data.get("success", False):
            return f"Failed to get document: {get_data.get('error', 'Unknown error')}"

        doc = get_data.get("document", {})
        if not doc:
            return f"No document found matching '{document_title}'"

        doc_id = doc.get("id")
        current_content = doc.get("content", {})

        if section_to_update in current_content:
            section_val = current_content[section_to_update]
            if isinstance(section_val, list):
                if new_content.startswith("[") and new_content.endswith("]"):
                    try:
                        current_content[section_to_update] = json.loads(new_content)
                    except Exception:
                        section_val.append(new_content)
                else:
                    section_val.append(new_content)
            elif isinstance(section_val, dict):
                try:
                    update_dict = json.loads(new_content)
                    section_val.update(update_dict)
                except Exception:
                    section_val["update"] = new_content
            else:
                current_content[section_to_update] = new_content
        else:
            try:
                current_content[section_to_update] = json.loads(new_content)
            except Exception:
                current_content[section_to_update] = new_content

        update_result = await mcp_client.manage_document(
            action="update",
            project_id=project_id,
            doc_id=doc_id,
            content=current_content,
            version=f"{float(doc.get('version', '1.0')) + 0.1:.1f}",
        )

        result_data = json.loads(update_result)
        if result_data.get("success"):
            return f"Successfully updated section '{section_to_update}' in document '{document_title}'. Change: {update_description}"
        return f"Failed to update document: {result_data.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        return f"Error updating document: {str(e)}"


async def create_feature_plan_logic(
    project_id: str,
    user_id: str | None,
    feature_name: str,
    feature_description: str,
    user_stories: str,
) -> str:
    """Logic for creating a feature plan with React Flow data."""
    try:
        nodes = [
            {
                "id": "start",
                "type": "input",
                "position": {"x": 100, "y": 100},
                "data": {"label": f"Start: {feature_name}"},
            }
        ]
        edges: list[dict[str, Any]] = []

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
        }

        mcp_client = await get_mcp_client()
        new_feature = {
            "id": str(uuid.uuid4()),
            "feature_type": "feature_plan",
            "name": feature_name,
            "title": f"{feature_name} - Feature Plan",
            "content": content,
            "created_by": user_id or "DocumentAgent",
        }

        result_json = await mcp_client.manage_project(
            action="add_feature", project_id=project_id, feature=new_feature
        )
        result_data = json.loads(result_json)

        if result_data.get("success", False):
            return f"Successfully created feature plan for '{feature_name}'."
        return f"Failed to create feature plan: {result_data.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error creating feature plan: {e}")
        return f"Error creating feature plan: {str(e)}"


async def create_erd_logic(
    project_id: str,
    user_id: str | None,
    system_name: str,
    entity_descriptions: str,
    relationships_description: str,
) -> str:
    """Logic for creating an ERD and SQL schema."""
    try:
        entities: list[dict[str, Any]] = []
        sql_schema: list[str] = []

        content = {
            "system_overview": {
                "name": system_name,
                "description": entity_descriptions,
            },
            "entities": entities,
            "database_schema": {"sql_statements": sql_schema},
        }

        mcp_client = await get_mcp_client()
        new_data_model = {
            "id": str(uuid.uuid4()),
            "data_type": "erd",
            "name": system_name,
            "title": f"{system_name} - Entity Relationship Diagram",
            "content": content,
            "created_by": user_id or "DocumentAgent",
        }

        result_json = await mcp_client.manage_project(
            action="add_data", project_id=project_id, data=new_data_model
        )
        result_data = json.loads(result_json)

        if result_data.get("success", False):
            return f"Successfully created ERD for '{system_name}'."
        return f"Failed to create ERD: {result_data.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error creating ERD: {e}")
        return f"Error creating ERD: {str(e)}"


async def request_approval_logic(
    project_id: str,
    user_id: str | None,
    document_title: str,
    change_summary: str,
    change_type: str = "update",
) -> str:
    """Logic for requesting document approval."""
    try:
        approval_content = {
            "approval_request": {
                "requested_by": user_id or "DocumentAgent",
                "request_date": datetime.now().isoformat(),
                "target_document": document_title,
                "change_type": change_type,
                "status": "pending_approval",
            },
            "change_summary": change_summary,
        }

        mcp_client = await get_mcp_client()
        result_json = await mcp_client.manage_document(
            action="create",
            project_id=project_id,
            document_type="approval_request",
            title=f"Approval Request: {document_title}",
            content=approval_content,
            tags=["approval", "workflow"],
            author=user_id or "DocumentAgent",
        )

        result_data = json.loads(result_json)
        if result_data.get("success", False):
            return f"Approval request created for '{document_title}'."
        return f"Failed to create approval request: {result_data.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error creating approval request: {e}")
        return f"Error creating approval request: {str(e)}"


# --- Helper functions ---


def _convert_to_blocks(
    title: str, document_type: str, content_description: str
) -> list[dict[str, Any]]:
    """FULL Jules implementation of block conversion including PRD sections."""
    blocks = [
        {
            "id": str(uuid.uuid4()),
            "type": "heading_1",
            "content": title,
            "properties": {"text": title},
        }
    ]

    if document_type == "prd":
        prd_sections = [
            "Project Overview",
            "Goals",
            "Scope",
            "Technical Requirements",
            "Architecture",
            "User Stories",
            "Timeline & Milestones",
            "Risks & Mitigations",
        ]
        for section in prd_sections:
            blocks.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "heading_2",
                    "content": section,
                    "properties": {"text": section},
                }
            )
            if section == "Project Overview":
                blocks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "paragraph",
                        "content": content_description,
                        "properties": {"text": content_description},
                    }
                )
    elif document_type == "technical_spec":
        tech_sections = ["Overview", "Technical Architecture", "API Design", "Database Schema"]
        for section in tech_sections:
            blocks.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "heading_2",
                    "content": section,
                    "properties": {"text": section},
                }
            )
    else:
        # Default fallback
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
