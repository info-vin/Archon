from collections.abc import Callable
from typing import Any

from supabase import Client

from ..config.logfire_config import get_logger
from ..services.client_manager import get_supabase_client

logger = get_logger(__name__)


class BaseRepository:
    def __init__(self, supabase_client: Client | None = None):
        self.supabase_client = supabase_client or get_supabase_client()
        self._token: str | None = None

    def set_user_context(self, token: str) -> "BaseRepository":
        """
        注入使用者的 JWT Token，確保後續查詢能觸發資料庫層的 RLS。
        """
        if token:
            self._token = token
            # 物理加固：更新 Supabase Client 的 Authorization 標頭
            self.supabase_client.postgrest.auth(token)
        return self

    def execute_query(
        self, query_func: Callable[[], Any], error_context: str = "Query failed", require_data: bool = False, max_retries: int = 1
    ) -> tuple[bool, dict[str, Any]]:
        """
        封裝 Supabase 查詢，提供標準化的錯誤處理與資料驗證機制。包含對 ConnectionTerminated 的自動重試 (自癒)。

        Args:
            query_func: 一個閉包或 lambda，回傳 Supabase 查詢的 response
            error_context: 錯誤紀錄時的上下文描述 (供前端介面與後端 Log 辨識)
            require_data: 如果此為 True，必定要求 response.data 不為空，否則視為 False
            max_retries: 遇到錯誤時的最多重試次數

        Returns:
            Tuple[bool, dict]: (成功與否, {"data": list/dict} 或 {"error": str})
        """
        import time

        last_exception = None
        for attempt in range(max_retries + 1):
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
                last_exception = e
                # Only retry on connection terminated or similar network/server errors
                error_str = str(e)
                if attempt < max_retries and ("ConnectionTerminated" in error_str or "RemoteProtocolError" in error_str or "ReadTimeout" in error_str):
                    logger.warning(f"⚠️ {error_context}: Connection dropped (attempt {attempt + 1}). Retrying...")
                    time.sleep(0.5)
                    continue
                break

        logger.error(f"{error_context}: {str(last_exception)}")
        return False, {"error": f"{error_context}: {str(last_exception)}"}
