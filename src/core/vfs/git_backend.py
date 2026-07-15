import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TrueGitBackend:
    """
    Virtual Filesystem (VFS) True Git Backend.
    Enforces that all human and agent actions trigger automatic commits to the underlying Git repository.
    Handles merge escalations to the LangGraph native interrupts.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            self._run_git(["init"])
            logger.info(f"Initialized new Git VFS at {self.workspace_path}")

    def _run_git(self, args: list[str]) -> str:
        """Executes a git command in the workspace directory."""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd, 
                cwd=str(self.workspace_path), 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if "conflict" in e.stdout.lower() or "conflict" in e.stderr.lower():
                from src.agents.concurrency import concurrency_manager
                concurrency_manager.escalate_merge_conflict(e.stdout + "\n" + e.stderr)
            logger.error(f"Git command failed: {e.stderr}")
            raise RuntimeError(f"VFS Git Error: {e.stderr}")

    def commit_changes(self, author: str, message: str):
        """
        Commits all current changes in the VFS to the Git history.
        The author indicates whether it was an Agent or Human Supervisor.
        """
        self._run_git(["add", "."])
        
        # Check if there's anything to commit
        status = self._run_git(["status", "--porcelain"])
        if not status:
            logger.debug("No changes to commit in VFS.")
            return

        self._run_git(["commit", "--author", f"{author} <{author}@coreason.ai>", "-m", message])
        logger.info(f"VFS Commit by {author}: {message}")

    def resolve_merge_conflict(self, resolution_data: str):
        """
        Placeholder for when the LangGraph interrupts for a human to resolve a conflict.
        The human uses the Cloud IDE to fix it, then calls this method to finalize the merge.
        """
        # 1. Write the resolution data to the files
        # 2. Add and commit
        pass

    def get_file_content(self, relative_path: str) -> str:
        """Reads a file from the VFS."""
        file_path = self.workspace_path / relative_path
        if not file_path.exists():
            raise FileNotFoundError(f"File {relative_path} not found in VFS.")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file_content(self, relative_path: str, content: str, author: str, commit_msg: str):
        """Writes to a file in the VFS and automatically commits."""
        file_path = self.workspace_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        self.commit_changes(author=author, message=commit_msg)
