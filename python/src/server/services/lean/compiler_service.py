# python/src/server/services/lean/compiler_service.py

import os
import re
import subprocess
from typing import Any

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

class LeanCompilerService:
    """Service to physical build/compile Lean 4 files and parse errors."""

    def __init__(self, lean_proofs_dir: str | None = None) -> None:
        if lean_proofs_dir:
            self.lean_proofs_dir = lean_proofs_dir
        else:
            # Fallback path finding relative to this file
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
            self.lean_proofs_dir = os.path.join(base_dir, "lean_proofs")

    def run_build(self) -> dict[str, Any]:
        """Runs `lake build` in the lean_proofs directory."""
        if not os.path.exists(self.lean_proofs_dir):
            return {
                "success": False,
                "error": f"lean_proofs directory not found at: {self.lean_proofs_dir}",
                "errors": []
            }

        try:
            logger.info(f"Running 'lake build' in {self.lean_proofs_dir}")
            # Use lake build inside subprocess
            result = subprocess.run(
                ["lake", "build"],
                cwd=self.lean_proofs_dir,
                capture_output=True,
                text=True,
                check=False
            )

            success = result.returncode == 0
            stdout_err = result.stdout + "\n" + result.stderr
            parsed_errors = self.parse_lake_errors(stdout_err)

            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "errors": parsed_errors
            }
        except Exception as e:
            logger.error(f"Failed to execute lake build: {e}")
            return {
                "success": False,
                "error": str(e),
                "errors": []
            }

    def parse_lake_errors(self, output: str) -> list[dict[str, Any]]:
        """Parses standard Lean 4 error output into a list of structured JSON errors.

        Example output format:
        /path/to/file.lean:line:col: error: message description
        """
        errors = []
        # Pattern to capture filename, line, col, and message
        # Format: path/to/file.lean:line:col: error: message
        pattern = re.compile(r"([^\s\n]+.lean):(\d+):(\d+):\s*error:\s*(.*)", re.MULTILINE)

        # We also need to capture multi-line messages until the next file path or empty line
        lines = output.splitlines()
        current_error = None

        for line in lines:
            match = pattern.search(line)
            if match:
                if current_error:
                    errors.append(current_error)
                file_path = match.group(1)
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                msg = match.group(4).strip()
                current_error = {
                    "file": file_path,
                    "line": line_num,
                    "column": col_num,
                    "message": msg
                }
            elif current_error and line.strip():
                # Append to current multiline message
                current_error["message"] = str(current_error["message"]) + "\n" + line.strip()
            elif current_error and not line.strip():
                errors.append(current_error)
                current_error = None

        if current_error:
            errors.append(current_error)

        return errors

lean_compiler_service = LeanCompilerService()
