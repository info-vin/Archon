import uuid
from typing import Any


def generate_feature_plan_content(feature_name: str, feature_description: str, user_stories: str) -> dict[str, Any]:
    """Generates the initial content structure for a Feature Plan."""
    nodes = [
        {
            "id": "start",
            "type": "input",
            "position": {"x": 100, "y": 100},
            "data": {"label": f"Start: {feature_name}"},
        }
    ]
    edges: list[dict[str, Any]] = []

    return {
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


def generate_erd_content(system_name: str, entity_descriptions: str) -> dict[str, Any]:
    """Generates the initial content structure for an ERD."""
    entities: list[dict[str, Any]] = []
    sql_schema: list[str] = []

    return {
        "system_overview": {
            "name": system_name,
            "description": entity_descriptions,
        },
        "entities": entities,
        "database_schema": {"sql_statements": sql_schema},
    }


def generate_document_blocks(title: str, document_type: str, content_description: str) -> list[dict[str, Any]]:
    """Generates the initial blocks for standard documents like PRDs and Tech Specs."""
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
