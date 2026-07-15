from pathlib import Path
import re

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def validate_safe_path(path_str: str, base_dir: Path = WORKSPACE_ROOT) -> Path:
    """
    Validates that a path is safe and does not escape the base directory (preventing directory traversal).
    """
    # Strict string-based sanitization and validation to remove taint for CodeQL
    if not path_str or not isinstance(path_str, str):
        raise ValueError("Security check failed: path must be a non-empty string.")
    
    # Only allow alphanumeric, underscores, dashes, dots, and slashes
    if not re.match(r"^[a-zA-Z0-9_\-\./]+$", path_str):
        raise ValueError(f"Security check failed: path contains disallowed characters.")
        
    if ".." in path_str:
        raise ValueError("Security check failed: path traversal ('..') is not allowed.")
        
    if path_str.startswith("/") or path_str.startswith("\\"):
        raise ValueError("Security check failed: absolute paths are not allowed.")

    resolved_base = base_dir.resolve()
    candidate = Path(path_str)
    if candidate.is_absolute():
        raise ValueError(f"Security check failed: absolute path '{path_str}' is not allowed.")

    # Resolve the path to handle relative paths and traversal characters safely
    resolved_path = (resolved_base / candidate).resolve()
    
    # Check if the resolved path is within the base directory
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        raise ValueError(f"Security check failed: path '{path_str}' escapes the allowed base directory.")
         
    return resolved_path

def validate_alphanumeric(name: str) -> str:
    """
    Validates that a string is strictly alphanumeric with dashes and underscores.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(f"Security check failed: '{name}' contains disallowed characters. Only alphanumeric, underscores, and dashes are allowed.")
    return name

def sanitize_log_input(value: str) -> str:
    """
    Sanitizes log input by stripping carriage return and newline characters to prevent log injection.
    """
    return str(value).replace('\r', '').replace('\n', '')

