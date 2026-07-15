from pathlib import Path
import re

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def validate_safe_path(path_str: str, base_dir: Path = WORKSPACE_ROOT) -> Path:
    """
    Validates that a path is safe and does not escape the base directory (preventing directory traversal).
    """
    resolved_base = base_dir.resolve()
    # Resolve the path to handle relative paths and traversal characters safely
    resolved_path = Path(resolved_base / path_str).resolve()
    
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

