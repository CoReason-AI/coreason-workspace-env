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
            result = subprocess.run(  # nosec B603
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
        
        status = self._run_git(["status", "--porcelain"])
        if not status:
            logger.debug("No changes to commit in VFS.")
            return

        self._run_git(["commit", "--author", f"{author} <{author}@coreason.ai>", "-m", message])
        logger.info(f"VFS Commit by {author}: {message}")

    def resolve_merge_conflict(self, resolution_data: str):
        """
        Placeholder for when the LangGraph interrupts for a human to resolve a conflict.
        """
        pass

    # --- BackendProtocol Implementation ---

    def read(self, path: str) -> str:
        """Reads a file from the VFS."""
        file_path = self.workspace_path / path
        if not file_path.exists():
            raise FileNotFoundError(f"File {path} not found in VFS.")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, path: str, content: str) -> None:
        """Writes to a file in the VFS and automatically commits."""
        file_path = self.workspace_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        self.commit_changes(author="Agent", message=f"VFS Backend write to {path}")

    def edit(self, path: str, content: str) -> None:
        """Edits a file in the VFS."""
        self.write(path, content)

    def ls(self, path: str = ".") -> list[str]:
        """Lists directory contents."""
        target_path = self.workspace_path / path
        if not target_path.exists():
            return []
        if target_path.is_file():
            return [path]
        return [str(p.relative_to(self.workspace_path)) for p in target_path.iterdir()]

    def grep(self, query: str, path: str = ".") -> str:
        """Searches for a string within the VFS."""
        # Stub for deepagents protocol compliance
        return ""

    def glob(self, pattern: str) -> list[str]:
        """Globs a pattern within the VFS."""
        # Stub for deepagents protocol compliance
        return []
