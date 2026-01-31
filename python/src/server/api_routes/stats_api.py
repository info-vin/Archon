"""
Stats API endpoints for Archon

Handles:
- Task distribution statistics (Tasks by Status)
- Team performance metrics (Member Performance)
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/tasks-by-status")
async def get_tasks_by_status():
    """
    Get the count of tasks grouped by status.
    Returns: List of { name: status, value: count }
    """
    try:
        logger.info("Fetching task distribution stats")
        supabase = get_supabase_client()

        # Optimization: Create a DB function for this in the future if data grows large.
        # Current approach: Fetch only 'status' field.
        response = supabase.table("archon_tasks").select("status").execute()

        # Aggregate in Python
        status_counts: dict[str, int] = {}
        for row in response.data:
            s = row.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        # Format for Recharts
        result = [
            {"name": status, "value": count}
            for status, count in status_counts.items()
        ]

        logger.info(f"Task stats retrieved | statuses={list(status_counts.keys())}")
        return result

    except Exception as e:
        logger.error(f"Failed to get task stats | error={str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        ) from e


@router.get("/member-performance")
async def get_member_performance():
    """
    Get the count of COMPLETED tasks grouped by assignee.
    Returns: List of { name: assignee, completed_tasks: count }
    """
    try:
        logger.info("Fetching member performance stats")
        supabase = get_supabase_client()

        # Fetch 'assignee' for all tasks where status is 'done'
        response = supabase.table("archon_tasks") \
            .select("assignee") \
            .eq("status", "done") \
            .execute()

        # Aggregate in Python
        member_counts: dict[str, int] = {}
        for row in response.data:
            assignee = row.get("assignee", "Unassigned")
            member_counts[assignee] = member_counts.get(assignee, 0) + 1

        # Format and Sort (Top performers first)
        result: list[dict[str, Any]] = [
            {"name": assignee, "completed_tasks": count}
            for assignee, count in member_counts.items()
        ]
        result.sort(key=lambda x: x["completed_tasks"], reverse=True)

        # Limit to top 10
        result = result[:10]

        logger.info(f"Performance stats retrieved | members_count={len(result)}")
        return result

    except Exception as e:
        logger.error(f"Failed to get performance stats | error={str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        ) from e

@router.get("/ai-usage")
async def get_ai_usage():
    """
    Get AI token usage statistics.
    Aggregates from gemini_logs (estimating 500 tokens per call).
    """
    try:
        logger.info("Fetching AI usage stats")
        supabase = get_supabase_client()

        # 1. Fetch logs
        # Note: In production, use count() or a dedicated stats table
        response = supabase.table("gemini_logs").select("user_name").execute()

        logs = response.data
        total_calls = len(logs)
        estimated_used = total_calls * 500

        # 2. Breakdown by User
        user_counts: dict[str, int] = {}
        for log in logs:
            user = log.get("user_name") or "Unknown"
            user_counts[user] = user_counts.get(user, 0) + 1

        breakdown: list[dict[str, Any]] = [
            {"name": user, "calls": count, "tokens": count * 500}
            for user, count in user_counts.items()
        ]
        breakdown.sort(key=lambda x: x["tokens"], reverse=True)

        return {
            "total_budget": 100000, # Hard limit for now
            "total_used": estimated_used,
            "usage_percentage": round((estimated_used / 100000) * 100, 1),
            "usage_by_user": breakdown
        }

    except Exception as e:
        logger.error(f"Failed to get AI usage stats | error={str(e)}")
        # Return fallback data instead of crashing UI
        return {
            "total_budget": 100000,
            "total_used": 0,
            "usage_percentage": 0,
            "usage_by_user": []
        }
