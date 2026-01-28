
import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)

class CodeModifier:
    """
    A utility class to safely modify code by creating a sandbox (git branch).
    It ensures that changes are isolated and can be easily reverted.
    """

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def _run_git(self, args: list[str]) -> str:
        """Helper to run git commands."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.base_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: git {' '.join(args)}\nStderr: {e.stderr}")
            raise RuntimeError(f"Git operation failed: {e.stderr}") from e

    def create_sandbox_branch(self, task_id: str) -> str:
        """
        Creates a temporary branch for the task.
        Format: autosave/fix-{task_id}-{timestamp}
        """
        timestamp = int(time.time())
        # Sanitize task_id for branch name
        safe_task_id = "".join(c if c.isalnum() else "-" for c in task_id).strip("-")
        branch_name = f"autosave/fix-{safe_task_id}-{timestamp}"

        logger.info(f"Creating sandbox branch: {branch_name}")

        # Ensure we are clean or handle dirty state?
        # For now, strict mode: require clean state or stash?
        # Let's try to just checkout -b. If it fails, we bubble up error.
        self._run_git(["checkout", "-b", branch_name])
        return branch_name

    def apply_modification(self, file_path: str, new_content: str):
        """
        Overwrites the file at file_path with new_content.
        """
        full_path = os.path.join(self.base_path, file_path)
        logger.info(f"Applying modification to: {full_path}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def revert_sandbox(self, original_branch: str):
        """
        Discards the current sandbox (if checked out) and returns to original_branch.
        WARNING: This does a hard reset/delete of the sandbox.
        """
        current_branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])

        if current_branch == original_branch:
             logger.warning("Already on original branch, nothing to revert.")
             return

        logger.info(f"Reverting sandbox. Switching back to {original_branch} and deleting {current_branch}")
        self._run_git(["checkout", original_branch])
        self._run_git(["branch", "-D", current_branch])

    def get_current_branch(self) -> str:
        return self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
