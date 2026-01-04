"""
Stats API endpoints for Archon

Handles:
- Task distribution statistics (Tasks by Status)
- Team performance metrics (Member Performance)
"""

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from ..config.logfire_config import get_logger, logfire
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
        logfire.info("Fetching task distribution stats")
        supabase = get_supabase_client()
        
        # We need to perform aggregation. Since Supabase-py doesn't support direct GROUP BY easily 
        # without RPC, we will fetch all tasks (lightweight) and aggregate in Python 
        # OR use a raw SQL query if we had a direct connection, but here we use the client.
        # Alternatively, checking if a dedicated RPC exists would be better, but for now 
        # fetching "status" column only is efficient enough for moderate datasets.
        
        # Optimization: Create a DB function for this in the future if data grows large.
        # Current approach: Fetch only 'status' field.
        response = supabase.table("archon_tasks").select("status").execute()
        
        # Aggregate in Python
        status_counts = {}
        for row in response.data:
            s = row.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1
            
        # Format for Recharts
        result = [
            {"name": status, "value": count}
            for status, count in status_counts.items()
        ]
        
        logfire.info(f"Task stats retrieved | statuses={list(status_counts.keys())}")
        return result

    except Exception as e:
        logfire.error(f"Failed to get task stats | error={str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"error": str(e)}
        )


@router.get("/member-performance")
async def get_member_performance():
    """
    Get the count of COMPLETED tasks grouped by assignee.
    Returns: List of { name: assignee, completed_tasks: count }
    """
    try:
        logfire.info("Fetching member performance stats")
        supabase = get_supabase_client()
        
        # Fetch 'assignee' for all tasks where status is 'done'
        response = supabase.table("archon_tasks") \
            .select("assignee") \
            .eq("status", "done") \
            .execute()
            
        # Aggregate in Python
        member_counts = {}
        for row in response.data:
            assignee = row.get("assignee", "Unassigned")
            member_counts[assignee] = member_counts.get(assignee, 0) + 1
            
        # Format and Sort (Top performers first)
        result = [
            {"name": assignee, "completed_tasks": count}
            for assignee, count in member_counts.items()
        ]
        result.sort(key=lambda x: x["completed_tasks"], reverse=True)
        
        # Limit to top 10
        result = result[:10]
        
        logfire.info(f"Performance stats retrieved | members_count={len(result)}")
        return result

    except Exception as e:
        logfire.error(f"Failed to get performance stats | error={str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"error": str(e)}
        )
