from typing import Any

from fastapi import HTTPException


def handle_service_result(
    success: bool,
    result: dict[str, Any] | list[Any] | str | None,
    not_found_msg: str = "not found"
) -> dict[str, Any] | list[Any]:
    """
    Standardizes the error checking for service layer responses.
    If success is False, parses the result to raise a 404 or 500 HTTPException.
    Returns the result directly if successful.
    """
    if not success:
        error_msg = ""
        detail = result

        if isinstance(result, dict) and "error" in result:
            error_msg = str(result["error"]).lower()
        elif isinstance(result, str):
            error_msg = result.lower()
            detail = {"error": result}

        if not_found_msg.lower() in error_msg:
            raise HTTPException(status_code=404, detail=detail)

        raise HTTPException(status_code=500, detail=detail)

    return result # type: ignore
