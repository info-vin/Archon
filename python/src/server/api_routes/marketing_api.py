from fastapi import APIRouter, HTTPException, Query
from typing import List

from ..config.logfire_config import get_logger, logfire
from ..services.job_board_service import JobBoardService, JobData

logger = get_logger(__name__)

router = APIRouter(prefix="/api/marketing", tags=["marketing"])

@router.get("/jobs", response_model=List[JobData])
async def search_jobs(keyword: str = Query(..., min_length=1), limit: int = 10):
    """
    Search for jobs using the JobBoardService.
    """
    try:
        logfire.info(f"API: Searching jobs | keyword={keyword}")
        jobs = await JobBoardService.search_jobs(keyword, limit)
        return jobs
    except Exception as e:
        logfire.error(f"API: Job search failed | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})
