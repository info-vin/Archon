from collections.abc import Callable
from typing import Any

from supabase import Client

from ..config.logfire_config import get_logger
from ..services.client_manager import get_supabase_client

logger = get_logger(__name__)


class BaseRepository:
    def __init__(self, supabase_client: Client | None = None):
        self.supabase_client = supabase_client or get_supabase_client()

    def execute_query(
        self, query_func: Callable[[], Any], error_context: str = "Query failed", require_data: bool = False
    ) -> tuple[bool, dict[str, Any]]:
        """
        封裝 Supabase 查詢，提供標準化的錯誤處理與資料驗證機制。

        Args:
            query_func: 一個閉包或 lambda，回傳 Supabase 查詢的 response
            error_context: 錯誤紀錄時的上下文描述 (供前端介面與後端 Log 辨識)
            require_data: 如果此為 True，必定要求 response.data 不為空，否則視為 False

        Returns:
            Tuple[bool, dict]: (成功與否, {"data": list/dict} 或 {"error": str})
        """
        try:
            response = query_func()
            if require_data and not response.data:
                return False, {"error": f"{error_context}"}

            # Include count metadata if available in the response
            result = {"data": response.data}
            if hasattr(response, "count") and response.count is not None:
                result["count"] = response.count

            return True, result
        except Exception as e:
            logger.error(f"{error_context}: {str(e)}")
            return False, {"error": f"{error_context}: {str(e)}"}
